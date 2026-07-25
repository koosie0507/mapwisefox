export const apiBase = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

type TokenResponse = {access_token?: unknown};
type AuthRequirement = {required?: unknown};

export type AuthState =
    | {status: "loading"}
    | {status: "disabled"}
    | {status: "authenticated"}
    | {status: "login-required"}
    | {status: "error"; message: string};

let accessToken: string | null = null;
let authEnabled = false;
let authState: AuthState = {status: "loading"};
let refreshPromise: Promise<boolean> | null = null;
const authListeners = new Set<() => void>();

export function apiUrl(path: string): string {
    return `${apiBase}${path.startsWith("/") ? path : `/${path}`}`;
}

function setAuthState(next: AuthState): void {
    authState = next;
    authListeners.forEach(listener => listener());
}

function setAuthenticated(): void {
    setAuthState({status: "authenticated"});
}

export function subscribeToAuth(listener: () => void): () => void {
    authListeners.add(listener);
    return () => authListeners.delete(listener);
}

export function getAuthState(): AuthState {
    return authState;
}

async function readAuthRequirement(): Promise<boolean | null> {
    try {
        const response = await fetch(apiUrl("/api/v1/auth/required"), {credentials: "include"});
        if (!response.ok) return null;
        const body = await response.json() as AuthRequirement;
        return typeof body.required === "boolean" ? body.required : null;
    } catch {
        return null;
    }
}

async function refreshAccessToken(): Promise<boolean> {
    if (!authEnabled) return true;
    if (refreshPromise) return refreshPromise;
    const pending = requestAccessToken();
    refreshPromise = pending;
    void pending.then(() => {
        if (refreshPromise === pending) refreshPromise = null;
    });
    return pending;
}

async function requestAccessToken(): Promise<boolean> {
    try {
        const response = await fetch(apiUrl("/auth/refresh"), {
            method: "POST",
            credentials: "include",
        });
        if (!response.ok) return markLoginRequired();
        const token = await response.json() as TokenResponse;
        if (typeof token.access_token !== "string" || !token.access_token) {
            return markLoginRequired();
        }
        accessToken = token.access_token;
        setAuthenticated();
        return true;
    } catch {
        return markLoginRequired();
    }
}

function markLoginRequired(): false {
    accessToken = null;
    console.error("Authentication is required to access the application.");
    setAuthState({status: "login-required"});
    return false;
}

export async function bootstrapAuth(): Promise<boolean> {
    const required = await readAuthRequirement();
    if (required === null) {
        setAuthState({status: "error", message: "Could not determine authentication requirements."});
        return false;
    }
    authEnabled = required;
    if (!required) {
        accessToken = null;
        setAuthState({status: "disabled"});
        return true;
    }
    return refreshAccessToken();
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
    const send = () => {
        const headers = new Headers(init.headers);
        if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
        return fetch(apiUrl(path), {...init, headers, credentials: "include"});
    };
    let response = await send();
    if (response.status === 401 && authEnabled && await refreshAccessToken()) response = await send();
    if (response.status === 401) markLoginRequired();
    return response;
}

export function login(): void {
    window.location.assign(`${apiUrl("/auth/login")}?return_to=${encodeURIComponent(window.location.href)}`);
}

export async function logout(): Promise<void> {
    try {
        const headers = new Headers();
        if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
        await fetch(apiUrl("/auth/logout"), {method: "POST", headers, credentials: "include"});
    } finally {
        accessToken = null;
        setAuthState(authEnabled ? {status: "login-required"} : {status: "disabled"});
    }
}
