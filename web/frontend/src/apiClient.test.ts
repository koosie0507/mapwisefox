import {afterEach, beforeEach, describe, expect, it, vi} from "vitest";

function jsonResponse(body: unknown, status = 200): Response {
    return new Response(JSON.stringify(body), {status});
}

describe("api client authentication", () => {
    beforeEach(() => {
        vi.resetModules();
        vi.stubGlobal("fetch", vi.fn());
    });

    afterEach(() => vi.unstubAllGlobals());

    it("boots without authentication when the server says it is disabled", async () => {
        vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({required: false}));
        const client = await import("./apiClient.ts");

        expect(await client.bootstrapAuth()).toBe(true);
        expect(client.getAuthState()).toEqual({status: "disabled"});
        expect(fetch).toHaveBeenCalledTimes(1);
    });

    it("refreshes an authenticated session during bootstrap", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: true}))
            .mockResolvedValueOnce(jsonResponse({access_token: "token"}));
        const client = await import("./apiClient.ts");

        expect(await client.bootstrapAuth()).toBe(true);
        expect(client.getAuthState()).toEqual({status: "authenticated"});
    });

    it("shows login when authentication discovery or refresh fails", async () => {
        vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({required: true}));
        const client = await import("./apiClient.ts");
        vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({}, 401));

        expect(await client.bootstrapAuth()).toBe(false);
        expect(client.getAuthState()).toEqual({status: "login-required"});
    });

    it("refreshes and retries a protected request once", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: true}))
            .mockResolvedValueOnce(jsonResponse({access_token: "token"}))
            .mockResolvedValueOnce(jsonResponse({}, 401))
            .mockResolvedValueOnce(jsonResponse({access_token: "new-token"}))
            .mockResolvedValueOnce(jsonResponse({ok: true}));
        const client = await import("./apiClient.ts");
        await client.bootstrapAuth();

        const response = await client.apiFetch("/api/v1/workbooks");

        expect(response.ok).toBe(true);
        expect(fetch).toHaveBeenCalledTimes(5);
    });

    it("clears authentication during logout", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: true}))
            .mockResolvedValueOnce(jsonResponse({access_token: "token"}))
            .mockResolvedValueOnce(new Response(null, {status: 204}));
        const client = await import("./apiClient.ts");
        await client.bootstrapAuth();
        await client.logout();

        expect(client.getAuthState()).toEqual({status: "login-required"});
    });

    it("fails closed on an unexpected unauthorized response", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: false}))
            .mockResolvedValueOnce(jsonResponse({}, 401));
        const client = await import("./apiClient.ts");
        await client.bootstrapAuth();

        await client.apiFetch("/api/v1/workbooks");

        expect(client.getAuthState()).toEqual({status: "login-required"});
    });
});
