import {cleanup, render, screen, waitFor} from "@testing-library/react";
import {afterEach, beforeEach, describe, expect, it, vi} from "vitest";

const config = {
    user: null,
    supportedFields: [{name: "title", mandatory: true}, {name: "authors", mandatory: true}],
    decisionColumn: "include",
    exclusionReasonColumn: "exclude_reason",
};

function jsonResponse(body: unknown, status = 200): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: {"Content-Type": "application/json"},
    });
}

function screeningResponse() {
    return {
        recordIndex: 0,
        recordCount: 1,
        decision: "undecided",
        exclusionReasons: [],
        evidence: {
            clusterId: 0,
            title: "A study",
            include: true,
            excludeReasons: [],
            keywords: [],
        },
        previousIndex: null,
        nextIndex: null,
        firstUndecidedIndex: 0,
        nextUndecidedIndex: null,
        complete: false,
        selectionCriteria: null,
    };
}

async function renderApp(path = "/"): Promise<void> {
    window.history.pushState({}, "", path);
    const {default: App} = await import("./App.tsx");
    render(<App/>);
}

describe("application composition", () => {
    beforeEach(() => {
        vi.resetModules();
        vi.stubGlobal("fetch", vi.fn());
    });

    afterEach(() => {
        cleanup();
        vi.unstubAllGlobals();
    });

    it("renders the home route when authentication is disabled", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: false}))
            .mockResolvedValueOnce(jsonResponse(config))
            .mockResolvedValueOnce(jsonResponse([]));

        await renderApp();

        expect(await screen.findByRole("heading", {name: "Primary study lists"})).toBeInTheDocument();
        expect(screen.getByRole("img", {name: "Mapwisefox"})).toBeInTheDocument();
        expect(screen.getByText("No surveys uploaded yet.")).toBeVisible();
    });

    it("shows login instead of protected content when refresh fails", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: true}))
            .mockResolvedValueOnce(jsonResponse({detail: "Authentication required"}, 401));

        await renderApp();

        expect(await screen.findByText("You must log in to use this app.")).toBeInTheDocument();
        expect(screen.queryByText("Primary Study Lists")).not.toBeInTheDocument();
    });

    it("renders the evidence route through the router facade", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: false}))
            .mockResolvedValueOnce(jsonResponse(config))
            .mockResolvedValueOnce(jsonResponse(screeningResponse()))
            .mockResolvedValueOnce(jsonResponse(screeningResponse()));

        await renderApp("/evidence/studies.xlsx");

        expect(await screen.findByRole("heading", {name: "[0] A study"})).toBeInTheDocument();
        await waitFor(() => expect(document.title).toBe("ERSA-SMS Survey - studies.xlsx"));
    });

    it("renders the not-found route", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: false}))
            .mockResolvedValueOnce(jsonResponse(config));

        await renderApp("/unknown");

        expect(await screen.findByRole("alert")).toHaveTextContent("Page not found.");
    });

    it("fails closed when authentication discovery fails", async () => {
        vi.mocked(fetch).mockResolvedValueOnce(jsonResponse({}, 503));

        await renderApp();

        expect(await screen.findByRole("alert")).toHaveTextContent("Could not determine authentication requirements.");
    });

    it("reports configuration failures before rendering a route", async () => {
        vi.mocked(fetch)
            .mockResolvedValueOnce(jsonResponse({required: false}))
            .mockResolvedValueOnce(jsonResponse({}, 503));

        await renderApp();

        expect(await screen.findByRole("alert")).toHaveTextContent("Could not load application configuration.");
    });
});
