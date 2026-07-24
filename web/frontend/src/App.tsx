import {useEffect, useState} from "react";
import Home from "./pages/Home.tsx";
import EvidencePage from "./pages/EvidencePage.tsx";

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
    const isHome = window.location.pathname === "/";
    const isEvidence = /^\/evidence\/[^/]+$/.test(window.location.pathname);

    useEffect(() => {
        void fetch("/api/v1/config").then(async response => {
            if (!response.ok) {
                setError(true);
                return;
            }
            setConfig(await response.json() as AppConfig);
        }).catch(() => setError(true));
    }, []);

    useEffect(() => {
        if (isHome) document.title = "ERSA-SMS Survey - Survey List";
    }, [isHome]);

    if (error) return <p role="alert">Could not load application configuration.</p>;
    if (!config) return null;

    return (
        <div className="root-container">
            {config.authEnabled && !config.user ? (
                <div className="login-container">
                    <p>You must log in to use this app.</p>
                    <form action="/auth/login" method="post">
                        <button type="submit" className="microsoft-btn">
                            <img
                                className="microsoft-logo"
                                src="https://upload.wikimedia.org/wikipedia/commons/4/44/Microsoft_logo.svg"
                                alt="Microsoft logo"
                            />
                            Log in with Microsoft
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
                                        <button type="submit" formAction="/auth/logout">
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
