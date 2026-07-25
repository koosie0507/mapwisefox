import {type FormEvent, useEffect, useState} from "react";
import {Link} from "react-router-dom";
import type {AppConfig} from "../models/config.ts";
import {deleteWorkbook as removeWorkbook, listWorkbooks, uploadWorkbook as importWorkbook, type Workbook} from "../api.ts";
import "../styles/home.css";

export default function Home({config}: {config: AppConfig}) {
    const [workbooks, setWorkbooks] = useState<Workbook[]>([]);
    const [operationStatus, setOperationStatus] = useState("");

    async function loadWorkbooks() {
        try {
            setWorkbooks(await listWorkbooks());
        } catch {
            setOperationStatus("Could not load workbooks.");
        }
    }

    useEffect(() => {
        void loadWorkbooks();
    }, []);

    async function deleteWorkbook(name: string) {
        try {
            await removeWorkbook(name);
            setOperationStatus("Workbook deleted.");
            await loadWorkbooks();
        } catch {
            setOperationStatus("Could not delete workbook.");
        }
    }

    async function uploadWorkbook(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        setOperationStatus("Uploading...");
        try {
            await importWorkbook(new FormData(event.currentTarget));
            setOperationStatus("Workbook imported.");
            await loadWorkbooks();
            return;
        } catch (error) {
            setOperationStatus(error instanceof Error ? error.message : "Could not import workbook.");
        }
    }

    return (
        <>
            <header className="header-container">
                {config.user && <p>Welcome, {config.user.display_name || config.user.email}</p>}
                <h1>Primary Study Lists</h1>
                <form className="upload" id="upload-form" encType="multipart/form-data" onSubmit={uploadWorkbook}>
                    <label htmlFor="workbook-file">Workbook file</label>
                    <input id="workbook-file" type="file" name="file" accept=".xlsx" required/>
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
                                    <Link to={`/evidence/${encodeURIComponent(workbook.name)}`}>Edit</Link>{" "}
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
