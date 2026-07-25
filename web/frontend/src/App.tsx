import {useEffect, useState, useSyncExternalStore, type ReactElement} from "react";
import {BrowserRouter, Link, Route, Routes} from "react-router-dom";
import {LogOut} from "lucide-react";
import Home from "./pages/Home.tsx";
import EvidencePage from "./pages/EvidencePage.tsx";
import {bootstrapAuth, getAuthState, login, logout, subscribeToAuth} from "./apiClient.ts";
import {getAppConfig} from "./api.ts";
import type {AppConfig} from "./models/config.ts";

function LoginPage(): ReactElement {
    return (
        <main className="login-container">
            <p>You must log in to use this app.</p>
            <form onSubmit={event => {
                event.preventDefault();
                login();
            }}>
                <button type="submit" className="provider-login-btn">Log in</button>
            </form>
        </main>
    );
}

function ErrorPage({message}: {message: string}): ReactElement {
    return <main className="main-container"><p role="alert">{message}</p></main>;
}

function NavigationHeader({authenticated}: {authenticated: boolean}): ReactElement {
    return (
        <header className="navigation-header">
            <nav className="toolbar" aria-label="Primary navigation">
                <div className="left-toolbar"><Link className="brand-link" to="/" aria-label="Mapwisefox home">
                    <img src="/mapwisefox-logo.png" alt="Mapwisefox"/>
                    <span>Survey List</span>
                </Link></div>
                {authenticated && <div className="right-toolbar">
                    <button type="button" onClick={() => void logout()}><LogOut aria-hidden="true" size={16}/> <span>Log out</span></button>
                </div>}
            </nav>
        </header>
    );
}

function AppRoutes({config, authenticated}: {config: AppConfig; authenticated: boolean}): ReactElement {
    return (
        <>
            <NavigationHeader authenticated={authenticated}/>
            <Routes>
                <Route path="/" element={<><Home config={config}/><Footer/></>}/>
                <Route path="/evidence/:fileName" element={<EvidencePage/>}/>
                <Route path="*" element={<ErrorPage message="Page not found."/>}/>
            </Routes>
        </>
    );
}

function Footer(): ReactElement {
    return <footer className="footer-container"><small>Entity Resolution Software Architecture - A systematic mapping study</small></footer>;
}

export default function App(): ReactElement {
    const auth = useSyncExternalStore(subscribeToAuth, getAuthState);
    const [config, setConfig] = useState<AppConfig | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        let active = true;
        void (async () => {
            if (!await bootstrapAuth()) return;
            if (active) setConfig(await getAppConfig());
        })().catch(() => {
            if (active) setError("Could not load application configuration.");
        });
        return () => { active = false; };
    }, []);

    if (auth.status === "login-required") return <LoginPage/>;
    if (auth.status === "error") return <ErrorPage message={auth.message}/>;
    if (error) return <ErrorPage message={error}/>;
    if (!config) return <main className="main-container"><p>Loading...</p></main>;

    return (
        <BrowserRouter>
            <div className="root-container">
                <AppRoutes config={config} authenticated={auth.status === "authenticated"}/>
            </div>
        </BrowserRouter>
    );
}
