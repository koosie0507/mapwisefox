import {type FormEvent, useEffect, useState} from "react";
import type {AppConfig} from "../App.tsx";
import "../styles/home.css";

type Workbook = {
    name: string;
    worksheetName: string;
    recordCount: number;
};

export default function Home({config}: {config: AppConfig}) {
    const [workbooks, setWorkbooks] = useState<Workbook[]>([]);
    const [operationStatus, setOperationStatus] = useState("");

    async function loadWorkbooks() {
        const response = await fetch("/api/v1/workbooks");
        if (!response.ok) {
            setOperationStatus("Could not load workbooks.");
            return;
        }
        setWorkbooks(await response.json() as Workbook[]);
    }

    useEffect(() => {
        void loadWorkbooks();
    }, []);

    async function deleteWorkbook(name: string) {
        const response = await fetch(`/api/v1/workbooks/${encodeURIComponent(name)}`, {method: "DELETE"});
        setOperationStatus(response.ok ? "Workbook deleted." : "Could not delete workbook.");
        if (response.ok) await loadWorkbooks();
    }

    async function uploadWorkbook(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setOperationStatus("Uploading...");
        const response = await fetch("/api/v1/workbooks", {
            method: "POST",
            body: new FormData(event.currentTarget),
        });
        if (response.ok) {
            setOperationStatus("Workbook imported.");
            await loadWorkbooks();
            return;
        }
        const body = await response.json() as {detail?: {message?: string} | string};
        setOperationStatus(
            typeof body.detail === "object" ? body.detail.message || "Could not import workbook." :
                body.detail || "Could not import workbook.",
        );
    }

    return (
        <>
            <header className="header-container">
                <form method="post">
                    <div className="toolbar">
                        <div className="left-toolbar"></div>
                        <div className="right-toolbar">
                            {config.authEnabled && (
                                <button type="submit" formAction="/auth/logout">
                                    <span className="emoji">⏻</span>Log out
                                </button>
                            )}
                        </div>
                    </div>
                </form>
                {config.user && <p>Welcome, {config.user.display_name || config.user.email}</p>}
                <h1>Primary Study Lists</h1>
                <form className="upload" id="upload-form" encType="multipart/form-data" onSubmit={uploadWorkbook}>
                    <input type="file" name="file" accept=".xlsx" required/>
                    <input type="text" name="worksheetName" defaultValue={config.worksheetName}
                           placeholder="Worksheet name" required/>
                    <input type="text" name="expectedColumns" defaultValue={config.expectedColumns}
                           placeholder="Expected columns (CSV)" required/>
                    <input type="hidden" name="decisionColumn" value={config.decisionColumn}/>
                    <input type="hidden" name="exclusionReasonColumn" value={config.exclusionReasonColumn}/>
                    <button type="submit">Upload</button>
                </form>
                <p id="operation-status" role="status">{operationStatus}</p>
            </header>
            <div className="file-list">
                <table>
                    <thead><tr><th>File Name</th><th>Worksheet</th><th>Records</th><th>Actions</th></tr></thead>
                    <tbody id="workbook-list">
                        {workbooks.map(workbook => (
                            <tr key={workbook.name}>
                                <td>{workbook.name}</td>
                                <td>{workbook.worksheetName}</td>
                                <td>{workbook.recordCount}</td>
                                <td>
                                    <a href={`/evidence/${encodeURIComponent(workbook.name)}`}>Edit</a>{" "}
                                    <button type="button" onClick={() => deleteWorkbook(workbook.name)}>Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                <p id="empty-list" hidden={workbooks.length > 0}>No files uploaded yet.</p>
            </div>
        </>
    );
}
