import {fireEvent, render, screen, waitFor} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import {beforeEach, describe, expect, it, vi} from "vitest";
import {MemoryRouter} from "react-router-dom";
import Home from "./Home.tsx";
import {deleteWorkbook, listWorkbooks, uploadWorkbook} from "../api.ts";

vi.mock("../api.ts", () => ({
    deleteWorkbook: vi.fn(),
    listWorkbooks: vi.fn(),
    uploadWorkbook: vi.fn(),
}));

const config = {
    user: {display_name: "Ada", email: "ada@example.com"},
    supportedFields: [{name: "title", mandatory: true}, {name: "authors", mandatory: true}],
    decisionColumn: "include",
    exclusionReasonColumn: "exclude_reason",
    backendVersion: "0.9.1",
};

const workbook = {name: "studies.xlsx", worksheetName: "Studies", recordCount: 2, unfilledRecordCount: 2};

describe("Home", () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(listWorkbooks).mockResolvedValue([]);
        vi.mocked(uploadWorkbook).mockResolvedValue(workbook);
        vi.mocked(deleteWorkbook).mockResolvedValue();
    });

    it("loads and displays workbooks and the user greeting", async () => {
        vi.mocked(listWorkbooks).mockResolvedValue([workbook]);
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);

        expect(await screen.findByText("studies.xlsx")).toBeInTheDocument();
        expect(screen.getByText("Welcome, Ada")).toBeInTheDocument();
        expect(screen.getByText("0 / 2 complete")).toBeInTheDocument();
        expect(screen.queryByText("No surveys uploaded yet.")).not.toBeVisible();
    });

    it("shows the empty state when loading fails", async () => {
        vi.mocked(listWorkbooks).mockRejectedValue(new Error("offline"));
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);

        expect(await screen.findByRole("status")).toHaveTextContent("Could not load workbooks.");
        expect(screen.getByText("No surveys uploaded yet.")).toBeVisible();
    });

    it("uploads and deletes workbooks", async () => {
        const user = userEvent.setup();
        vi.mocked(listWorkbooks).mockResolvedValueOnce([]).mockResolvedValue([workbook]);
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);
        const file = new File(["xlsx"], "studies.xlsx", {type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});
        const criteria = new File(["{}"], "criteria.json", {type: "application/json"});

        await user.upload(screen.getByLabelText("Workbook file"), file);
        await user.upload(screen.getByLabelText("Selection criteria (optional, .json)"), criteria);
        fireEvent.submit(screen.getByRole("button", {name: "Upload"}).closest("form")!);
        await waitFor(() => expect(uploadWorkbook).toHaveBeenCalled());
        expect(uploadWorkbook).toHaveBeenCalledWith(expect.any(FormData));
        const sent = vi.mocked(uploadWorkbook).mock.calls[0][0] as FormData;
        expect(sent.get("file")).toBeInstanceOf(File);
        expect(sent.get("selectionCriteria")).toBeInstanceOf(File);
        expect(sent.get("worksheetName")).toBeNull();
        expect(sent.get("fieldMappings")).toBeNull();
        expect(screen.getByRole("status")).toHaveTextContent("Workbook imported.");

        vi.mocked(listWorkbooks).mockResolvedValue([workbook]);
        await screen.findByText("studies.xlsx");
        await user.click(screen.getByRole("button", {name: "Delete studies.xlsx"}));
        await user.click(screen.getByRole("button", {name: "Yes"}));
        expect(await screen.findByRole("status")).toHaveTextContent("Workbook deleted.");
    });

    it("uploads a workbook without selection criteria", async () => {
        const user = userEvent.setup();
        vi.mocked(listWorkbooks).mockResolvedValueOnce([]).mockResolvedValue([workbook]);
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);
        const file = new File(["xlsx"], "studies.xlsx", {type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});

        await user.upload(screen.getByLabelText("Workbook file"), file);
        fireEvent.submit(screen.getByRole("button", {name: "Upload"}).closest("form")!);
        await waitFor(() => expect(uploadWorkbook).toHaveBeenCalled());
        const sent = vi.mocked(uploadWorkbook).mock.calls[0][0] as FormData;
        expect(sent.get("file")).toBeInstanceOf(File);
        const criteria = sent.get("selectionCriteria");
        expect(criteria === null || (criteria instanceof File && criteria.size === 0)).toBe(true);
    });

    it("submits an explicit field mapping", async () => {
        const user = userEvent.setup();
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);
        await user.type(screen.getByLabelText("Mapwisefox field"), "title");
        const workbookColumn = screen.getByLabelText("Workbook column");
        expect(workbookColumn).toHaveFocus();
        await user.type(workbookColumn, "article");
        await user.keyboard("{Enter}");
        expect(screen.getByText(/title=article/)).toBeInTheDocument();
        expect(uploadWorkbook).not.toHaveBeenCalled();
        const file = new File(["xlsx"], "studies.xlsx");

        await user.upload(screen.getByLabelText("Workbook file"), file);
        fireEvent.submit(screen.getByRole("button", {name: "Upload"}).closest("form")!);
        await waitFor(() => expect(uploadWorkbook).toHaveBeenCalled());

        const sent = vi.mocked(uploadWorkbook).mock.calls[0][0] as FormData;
        expect(sent.get("fieldMappings")).toBe('{"title":"article"}');
    });

    it("reports upload and delete failures", async () => {
        const user = userEvent.setup();
        vi.mocked(uploadWorkbook).mockRejectedValue(new Error("Invalid workbook"));
        vi.mocked(listWorkbooks).mockResolvedValue([workbook]);
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);
        const file = new File(["xlsx"], "studies.xlsx", {type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"});
        await user.upload(screen.getByLabelText("Workbook file"), file);
        fireEvent.submit(screen.getByRole("button", {name: "Upload"}).closest("form")!);
        await waitFor(() => expect(screen.getByRole("status")).toHaveTextContent("Invalid workbook"));

        vi.mocked(deleteWorkbook).mockRejectedValue(new Error("failed"));
        await user.click(screen.getByRole("button", {name: "Delete studies.xlsx"}));
        await user.click(screen.getByRole("button", {name: "Yes"}));
        expect(screen.getByRole("status")).toHaveTextContent("Could not delete workbook.");
    });

    it("cancels an inline deletion confirmation", async () => {
        const user = userEvent.setup();
        vi.mocked(listWorkbooks).mockResolvedValue([workbook]);
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);

        await screen.findByText("studies.xlsx");
        await user.click(screen.getByRole("button", {name: "Delete studies.xlsx"}));
        await user.click(screen.getByRole("button", {name: "No"}));

        expect(screen.getByRole("button", {name: "Delete studies.xlsx"})).toBeInTheDocument();
        expect(deleteWorkbook).not.toHaveBeenCalled();
    });

    it("keeps the upload form collapsed until requested", () => {
        render(<MemoryRouter><Home config={config}/></MemoryRouter>);

        expect(screen.getByText("Import a survey").closest("details")).not.toHaveAttribute("open");
    });
});
