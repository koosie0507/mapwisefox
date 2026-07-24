export const apiBase = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

type TokenResponse = {
    access_token: string;
};

let accessToken: string | null = null;
let authEnabled = false;
let authRequired = false;
let refreshPromise: Promise<boolean> | null = null;
const authListeners = new Set<() => void>();

export function apiUrl(path: string): string {
    return `${apiBase}${path.startsWith("/") ? path : `/${path}`}`;
}

function setAuthRequired(required: boolean) {
    if (authRequired === required) return;
    authRequired = required;
    authListeners.forEach(listener => listener());
}

export function subscribeToAuth(listener: () => void) {
    authListeners.add(listener);
    return () => authListeners.delete(listener);
}

export function getAuthRequired(): boolean {
    return authRequired;
}

export function setAuthEnabled(enabled: boolean) {
    authEnabled = enabled;
    if (!enabled) {
        accessToken = null;
        setAuthRequired(false);
    }
}

async function refreshAccessToken(): Promise<boolean> {
    if (!authEnabled) return true;
    if (refreshPromise) return refreshPromise;

    const pending = (async () => {
        try {
            const response = await fetch(apiUrl("/auth/refresh"), {
                method: "POST",
                credentials: "include",
            });
            if (!response.ok) {
                accessToken = null;
                setAuthRequired(true);
                return false;
            }

            const token = await response.json() as TokenResponse;
            if (!token.access_token) {
                accessToken = null;
                setAuthRequired(true);
                return false;
            }
            accessToken = token.access_token;
            setAuthRequired(false);
            return true;
        } catch {
            accessToken = null;
            setAuthRequired(true);
            return false;
        }
    })();

    refreshPromise = pending;
    void pending.finally(() => {
        if (refreshPromise === pending) refreshPromise = null;
    });
    return pending;
}

export async function bootstrapAuth(): Promise<void> {
    await refreshAccessToken();
}

export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
    const send = () => {
        const headers = new Headers(init.headers);
        if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
        return fetch(apiUrl(path), {...init, headers, credentials: "include"});
    };

    let response = await send();
    if (response.status === 401 && authEnabled && await refreshAccessToken()) {
        response = await send();
    }
    return response;
}

export function login() {
    window.location.assign(`${apiUrl("/auth/login")}?return_to=${encodeURIComponent(window.location.href)}`);
}

export async function logout(): Promise<void> {
    try {
        const headers = new Headers();
        if (accessToken) headers.set("Authorization", `Bearer ${accessToken}`);
        await fetch(apiUrl("/auth/logout"), {
            method: "POST",
            headers,
            credentials: "include",
        });
    } finally {
        accessToken = null;
        setAuthRequired(authEnabled);
    }
}
