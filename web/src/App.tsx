import { useEffect, useState } from "react";
import { LandingPage } from "./pages/LandingPage";
import { AppPage } from "./pages/AppPage";

function getCurrentRoute(): "landing" | "app" {
  const path = window.location.pathname.toLowerCase().replace(/\/+$/, "");
  if (path === "/app" || path.startsWith("/app/")) {
    return "app";
  }
  return "landing";
}

export default function App() {
  const [route, setRoute] = useState<"landing" | "app">(() => getCurrentRoute());

  useEffect(() => {
    const handlePopState = () => {
      setRoute(getCurrentRoute());
    };

    window.addEventListener("popstate", handlePopState);
    return () => {
      window.removeEventListener("popstate", handlePopState);
    };
  }, []);

  const navigateTo = (target: "landing" | "app") => {
    const path = target === "app" ? "/app" : "/";
    if (window.location.pathname !== path) {
      window.history.pushState({}, "", path);
      setRoute(target);
      window.scrollTo({ top: 0, behavior: "smooth" });
    }
  };

  if (route === "app") {
    return <AppPage onNavigateHome={() => navigateTo("landing")} />;
  }

  return <LandingPage onNavigateApp={() => navigateTo("app")} />;
}
