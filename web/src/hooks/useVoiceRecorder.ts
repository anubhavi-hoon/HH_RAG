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
  const chunksRef = useRef<BlobPart[]>([]);

  const releaseStream = useCallback(() => {
    recorderRef.current?.stream.getTracks().forEach((track) => track.stop());
    recorderRef.current = null;
  }, []);

  useEffect(() => releaseStream, [releaseStream]);

  const start = useCallback(async (): Promise<boolean> => {
    if (!isRecordingSupported()) {
      onError("Voice recording is not supported in this browser.");
      return false;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (error) {
      onError(microphoneErrorMessage(error));
      return false;
    }

    const mimeType = pickMimeType();
    let recorder: MediaRecorder;
    try {
      recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    } catch {
      stream.getTracks().forEach((track) => track.stop());
      onError("This browser could not record audio in a supported format.");
      return false;
    }

    chunksRef.current = [];
    recorder.ondataavailable = (event) => {
      if (event.data.size > 0) chunksRef.current.push(event.data);
    };
    recorder.onerror = () => {
      releaseStream();
      onError("Recording stopped unexpectedly.");
    };
    recorder.onstop = () => {
      const blob = new Blob(chunksRef.current, {
        type: recorder.mimeType || mimeType || "audio/webm",
      });
      chunksRef.current = [];
      releaseStream();
      if (blob.size === 0) {
        onError("No audio was captured. Check your microphone and try again.");
        return;
      }
      onComplete(blob);
    };

    recorderRef.current = recorder;
    recorder.start();
    return true;
  }, [onComplete, onError, releaseStream]);

  const stop = useCallback(() => {
    const recorder = recorderRef.current;
    if (recorder && recorder.state !== "inactive") {
      recorder.stop();
    }
  }, []);

  return { start, stop, isSupported: isRecordingSupported() };
}
