import {useEffect, useState, useSyncExternalStore} from "react";
import Home from "./pages/Home.tsx";
import EvidencePage from "./pages/EvidencePage.tsx";
import {
    apiFetch,
    bootstrapAuth,
    getAuthRequired,
    login,
    logout,
    setAuthEnabled,
    subscribeToAuth,
} from "./apiClient.ts";

export type AppConfig = {
    authEnabled: boolean;
    user: {
        display_name: string | null;
        email: string;
    } | null;
    worksheetName: string;
    expectedColumns: string;
    decisionColumn: string;
    exclusionReasonColumn: string;
};

export default function App() {
    const [config, setConfig] = useState<AppConfig | null>(null);
    const [error, setError] = useState(false);
    const authRequired = useSyncExternalStore(subscribeToAuth, getAuthRequired);
    const isHome = window.location.pathname === "/";
    const isEvidence = /^\/evidence\/[^/]+$/.test(window.location.pathname);

    useEffect(() => {
        void apiFetch("/api/v1/config").then(async response => {
            if (!response.ok) {
                setError(true);
                return;
            }
            const appConfig = await response.json() as AppConfig;
            setAuthEnabled(appConfig.authEnabled);
            await bootstrapAuth();
            if (!appConfig.authEnabled) {
                setConfig(appConfig);
                return;
            }
            const authenticatedResponse = await apiFetch("/api/v1/config");
            setConfig(authenticatedResponse.ok ? await authenticatedResponse.json() as AppConfig : appConfig);
        }).catch(() => setError(true));
    }, []);

    useEffect(() => {
        if (isHome) document.title = "ERSA-SMS Survey - Survey List";
    }, [isHome]);

    if (error) return <p role="alert">Could not load application configuration.</p>;
    if (!config) return null;

    return (
        <div className="root-container">
            {authRequired ? (
                <div className="login-container">
                    <p>You must log in to use this app.</p>
                    <form onSubmit={event => {
                        event.preventDefault();
                        login();
                    }}>
                        <button type="submit" className="provider-login-btn">
                            Log in
                        </button>
                    </form>
                </div>
            ) : isHome ? (
                <>
                    <Home config={config}/>
                    <footer className="footer-container">
                        <small>Entity Resolution Software Architecture - A systematic mapping study</small>
                    </footer>
                </>
            ) : isEvidence ? (
                <>
                    <header className="header-container">
                        <form method="post">
                            <div className="toolbar">
                                <div className="left-toolbar">
                                    <button type="submit" formAction="/" formMethod="get" title="Home">
                                        <span className="emoji">🏠</span>Survey List
                                    </button>
                                </div>
                                <div className="right-toolbar">
                                    {config.authEnabled && (
                                        <button type="button" onClick={() => void logout()}>
                                            <span className="emoji">⏻</span>Log out
                                        </button>
                                    )}
                                </div>
                            </div>
                        </form>
                    </header>
                    <EvidencePage/>
                </>
            ) : (
                <main className="main-container"><p>empty page...</p></main>
            )}
        </div>
    );
}
