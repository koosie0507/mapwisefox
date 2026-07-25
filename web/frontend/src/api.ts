import {apiFetch} from "./apiClient.ts";
import type {AppConfig} from "./models/config.ts";
import type {ScreeningResponse} from "./models/transfer.ts";

export type Workbook = {
    name: string;
    worksheetName: string;
    recordCount: number;
    unfilledRecordCount: number;
};

export class ApiError extends Error {
    readonly status: number;

    constructor(message: string, status: number) {
        super(message);
        this.name = "ApiError";
        this.status = status;
    }
}

function isRecord(value: unknown): value is Record<string, unknown> {
    return typeof value === "object" && value !== null;
}

function requiredString(value: unknown, field: string): string {
    if (typeof value !== "string") throw new Error(`Invalid API field: ${field}`);
    return value;
}

function parseConfig(value: unknown): AppConfig {
    if (!isRecord(value)) throw new Error("Invalid application configuration.");
    return {
        user: value.user === null ? null : parseUser(value.user),
        worksheetName: requiredString(value.worksheetName, "worksheetName"),
        expectedColumns: requiredString(value.expectedColumns, "expectedColumns"),
        decisionColumn: requiredString(value.decisionColumn, "decisionColumn"),
        exclusionReasonColumn: requiredString(value.exclusionReasonColumn, "exclusionReasonColumn"),
    };
}

function parseUser(value: unknown): NonNullable<AppConfig["user"]> {
    if (!isRecord(value)) throw new Error("Invalid application user.");
    return {
        display_name: value.display_name === null ? null : requiredString(value.display_name, "display_name"),
        email: requiredString(value.email, "email"),
    };
}

function parseWorkbook(value: unknown): Workbook {
    if (!isRecord(value)) throw new Error("Invalid workbook response.");
    return {
        name: requiredString(value.name, "name"),
        worksheetName: requiredString(value.worksheetName, "worksheetName"),
        recordCount: requiredNumber(value.recordCount, "recordCount"),
        unfilledRecordCount: requiredNumber(value.unfilledRecordCount, "unfilledRecordCount"),
    };
}

function requiredNumber(value: unknown, field: string): number {
    if (typeof value !== "number") throw new Error(`Invalid API field: ${field}`);
    return value;
}

function isScreeningResponse(value: unknown): value is ScreeningResponse {
    if (!isRecord(value) || !isRecord(value.evidence)) return false;
    return typeof value.recordIndex === "number"
        && typeof value.recordCount === "number"
        && typeof value.decision === "string"
        && Array.isArray(value.exclusionReasons)
        && typeof value.complete === "boolean";
}

function parseScreening(value: unknown): ScreeningResponse {
    if (!isScreeningResponse(value)) throw new Error("Invalid screening response.");
    return value;
}

async function responseBody(response: Response): Promise<unknown> {
    if (!response.ok) throw new ApiError(await errorMessage(response), response.status);
    if (response.status === 204) return null;
    return response.json();
}

async function errorMessage(response: Response): Promise<string> {
    try {
        const body = await response.json() as unknown;
        if (isRecord(body) && typeof body.detail === "string") return body.detail;
        if (isRecord(body) && isRecord(body.detail) && typeof body.detail.message === "string") {
            return body.detail.message;
        }
    } catch {
        return "Request failed.";
    }
    return "Request failed.";
}

export async function getAppConfig(): Promise<AppConfig> {
    return parseConfig(await responseBody(await apiFetch("/api/v1/config")));
}

export async function listWorkbooks(): Promise<Workbook[]> {
    const value = await responseBody(await apiFetch("/api/v1/workbooks"));
    if (!Array.isArray(value)) throw new Error("Invalid workbook response.");
    return value.map(parseWorkbook);
}

export async function uploadWorkbook(form: FormData): Promise<Workbook> {
    return parseWorkbook(await responseBody(await apiFetch("/api/v1/workbooks", {method: "POST", body: form})));
}

export async function deleteWorkbook(name: string): Promise<void> {
    await responseBody(await apiFetch(`/api/v1/workbooks/${encodeURIComponent(name)}`, {method: "DELETE"}));
}

export async function getScreening(resource: string, index: number): Promise<ScreeningResponse> {
    return parseScreening(await responseBody(await apiFetch(`${resource}/${index}`)));
}

export async function updateScreening(
    resource: string,
    index: string | number,
    decision: "included" | "excluded",
    exclusionReasons: string[],
): Promise<ScreeningResponse> {
    return parseScreening(await responseBody(await apiFetch(`${resource}/${index}`, {
        method: "PATCH",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({decision, exclusionReasons}),
    })));
}
