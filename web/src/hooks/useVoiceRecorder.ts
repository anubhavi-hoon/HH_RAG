/**
 * Thin MediaRecorder wrapper. Owns microphone lifecycle only — it never talks to
 * the API; the caller decides what to do with the produced Blob.
 */

import { useCallback, useEffect, useRef } from "react";

const PREFERRED_MIME_TYPES = [
  "audio/webm;codecs=opus",
  "audio/webm",
  "audio/ogg;codecs=opus",
  "audio/mp4",
  "audio/aac",
];

function pickMimeType(): string | undefined {
  if (typeof MediaRecorder === "undefined") return undefined;
  return PREFERRED_MIME_TYPES.find((type) => MediaRecorder.isTypeSupported(type));
}

export function isRecordingSupported(): boolean {
  return (
    typeof window !== "undefined" &&
    typeof MediaRecorder !== "undefined" &&
    Boolean(navigator.mediaDevices?.getUserMedia)
  );
}

function microphoneErrorMessage(error: unknown): string {
  const name = error instanceof DOMException ? error.name : "";
  switch (name) {
    case "NotAllowedError":
    case "PermissionDeniedError":
      return "Microphone access was denied. Allow it in your browser settings and try again.";
    case "NotFoundError":
    case "DevicesNotFoundError":
      return "No microphone was found on this device.";
    case "NotReadableError":
    case "TrackStartError":
      return "The microphone is already in use by another application.";
    case "SecurityError":
      return "Microphone access requires a secure context (https or localhost).";
    default:
      return "Could not start recording with this microphone.";
  }
}

interface RecorderOptions {
  onComplete: (audio: Blob) => void;
  onError: (message: string) => void;
}

export function useVoiceRecorder({ onComplete, onError }: RecorderOptions) {
  const recorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const chunksRef = useRef<BlobPart[]>([]);

  const cleanup = useCallback(() => {
    if (recorderRef.current && recorderRef.current.state !== "inactive") {
      try {
        recorderRef.current.stop();
      } catch {
        // Ignore stop errors during cleanup
      }
    }
    recorderRef.current = null;
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    chunksRef.current = [];
  }, []);

  useEffect(() => cleanup, [cleanup]);

  const start = useCallback(async (): Promise<boolean> => {
    if (!isRecordingSupported()) {
      onError("Voice recording is not supported in this browser.");
      return false;
    }

    // Ensure any previous recorder or stream is cleaned up
    cleanup();

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
    } catch (error) {
      onError(microphoneErrorMessage(error));
      return false;
    }

    const mimeType = pickMimeType();
    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    } catch {
      cleanup();
      onError("This browser could not record audio in a supported format.");
      return false;
    }

    // Fresh chunk array for this recording session
    chunksRef.current = [];

    recorder.ondataavailable = (event: BlobEvent) => {
      if (event.data && event.data.size > 0) {
        chunksRef.current.push(event.data);
      }
    };

    recorder.onerror = () => {
      cleanup();
      onError("Recording stopped unexpectedly.");
    };

    recorder.onstop = () => {
      const currentChunks = [...chunksRef.current];
      chunksRef.current = [];

      const activeMime = recorder.mimeType || mimeType || "audio/webm";
      const blob = new Blob(currentChunks, { type: activeMime });

      // Stop audio tracks after recording completion
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }
      recorderRef.current = null;

      console.info(
        `[VoiceRecorder] Finalized recording | Chunks: ${currentChunks.length} | Size: ${blob.size} bytes | MIME: ${activeMime}`
      );

      if (blob.size === 0) {
        onError("No audio was captured. Check your microphone and try again.");
        return;
      }

      onComplete(blob);
    };

    recorderRef.current = recorder;
    // Collect chunks every 250ms for reliable audio stream capture
    recorder.start(250);
    return true;
  }, [cleanup, onComplete, onError]);

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state === "recording") {
      recorder.stop();
    }
  }, []);

  return { start, stop, isSupported: isRecordingSupported() };
}
