import {beforeEach, describe, expect, it, vi} from "vitest";
import {apiFetch} from "./apiClient.ts";
import {ApiError, deleteWorkbook, getAppConfig, getScreening, listWorkbooks, updateScreening, uploadWorkbook} from "./api.ts";

vi.mock("./apiClient.ts", () => ({apiFetch: vi.fn()}));

function jsonResponse(body: unknown, status = 200): Response {
    return new Response(JSON.stringify(body), {status});
}

const config = {
    user: {display_name: "Ada", email: "ada@example.com"},
    supportedFields: [{name: "title", mandatory: true}, {name: "authors", mandatory: true}],
    decisionColumn: "include",
    exclusionReasonColumn: "exclude_reason",
};

const workbook = {name: "study.xlsx", worksheetName: "Studies", recordCount: 1, unfilledRecordCount: 1};
const screening = {
    recordIndex: 0,
    recordCount: 1,
    decision: "undecided",
    exclusionReasons: [],
    evidence: {clusterId: 0, title: "Study", include: true, excludeReasons: [], keywords: []},
    previousIndex: null,
    nextIndex: null,
    firstUndecidedIndex: 0,
    nextUndecidedIndex: null,
    complete: false,
    selectionCriteria: null,
};

describe("API facade", () => {
    beforeEach(() => vi.mocked(apiFetch).mockReset());

    it("parses configuration, workbooks, and screening responses", async () => {
        vi.mocked(apiFetch)
            .mockResolvedValueOnce(jsonResponse(config))
            .mockResolvedValueOnce(jsonResponse([workbook]))
            .mockResolvedValueOnce(jsonResponse(workbook))
            .mockResolvedValueOnce(new Response(null, {status: 204}))
            .mockResolvedValueOnce(jsonResponse(screening))
            .mockResolvedValueOnce(jsonResponse(screening));

        expect(await getAppConfig()).toEqual(config);
        expect(await listWorkbooks()).toEqual([workbook]);
        expect(await uploadWorkbook(new FormData())).toEqual(workbook);
        await deleteWorkbook("study.xlsx");
        expect(await getScreening("/screening", 0)).toEqual(screening);
        expect(await updateScreening("/screening", 0, "included", [])).toEqual(screening);
    });

    it("reports malformed successful responses", async () => {
        vi.mocked(apiFetch).mockResolvedValueOnce(jsonResponse({user: null}));
        await expect(getAppConfig()).rejects.toThrow("Invalid API field: supportedFields");
        vi.mocked(apiFetch).mockResolvedValueOnce(jsonResponse({}));
        await expect(listWorkbooks()).rejects.toThrow("Invalid workbook response.");
        vi.mocked(apiFetch).mockResolvedValueOnce(jsonResponse([{name: "x"}]));
        await expect(listWorkbooks()).rejects.toThrow("Invalid API field: worksheetName");
        vi.mocked(apiFetch).mockResolvedValueOnce(jsonResponse({}));
        await expect(getScreening("/screening", 0)).rejects.toThrow("Invalid screening response.");
    });

    it("normalizes structured, plain, and empty API failures", async () => {
        vi.mocked(apiFetch).mockResolvedValueOnce(jsonResponse({detail: {message: "Bad workbook"}}, 422));
        await expect(uploadWorkbook(new FormData())).rejects.toEqual(new ApiError("Bad workbook", 422));
        vi.mocked(apiFetch).mockResolvedValueOnce(jsonResponse({detail: "Unauthorized"}, 401));
        await expect(getScreening("/screening", 0)).rejects.toThrow("Unauthorized");
        vi.mocked(apiFetch).mockResolvedValueOnce(new Response("not json", {status: 500}));
        await expect(deleteWorkbook("study.xlsx")).rejects.toThrow("Request failed.");
    });
});
