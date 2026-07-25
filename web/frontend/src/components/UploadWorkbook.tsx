import {useRef, type FormEvent} from "react";
import type {AppConfig} from "../models/config.ts";
import styles from "../pages/Home.module.css";

type UploadWorkbookProps = {
    config: AppConfig;
    onUpload: (formData: FormData, reset: () => void) => Promise<void>;
};

export default function UploadWorkbook({config, onUpload}: UploadWorkbookProps) {
    const formRef = useRef<HTMLFormElement>(null);

    function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        void onUpload(new FormData(event.currentTarget), () => formRef.current?.reset());
    }

    return <details className={styles.uploadDetails}>
        <summary>Import a survey</summary>
        <form ref={formRef} className={styles.uploadForm} encType="multipart/form-data" onSubmit={submit}>
            <label htmlFor="workbook-file">Workbook file</label>
            <input id="workbook-file" type="file" name="file" accept=".xlsx" required/>
            <input type="text" name="worksheetName" defaultValue={config.worksheetName} placeholder="Worksheet name" required/>
            <input type="text" name="expectedColumns" defaultValue={config.expectedColumns} placeholder="Expected columns (CSV)" required/>
            <input type="hidden" name="decisionColumn" value={config.decisionColumn}/>
            <input type="hidden" name="exclusionReasonColumn" value={config.exclusionReasonColumn}/>
            <button type="submit">Upload</button>
        </form>
    </details>;
}
