import {useRef, useState, type FormEvent} from "react";
import type {AppConfig} from "../models/config.ts";
import styles from "../pages/Home.module.css";

type UploadWorkbookProps = {
    config: AppConfig;
    onUpload: (formData: FormData, reset: () => void) => Promise<void>;
};

export default function UploadWorkbook({config, onUpload}: UploadWorkbookProps) {
    const formRef = useRef<HTMLFormElement>(null);
    const [mappings, setMappings] = useState<Array<{field: string; column: string}>>([]);
    const [field, setField] = useState("");
    const [column, setColumn] = useState("");
    const allowedFields = config.supportedFields.filter(({name}) => !mappings.some((mapping) => mapping.field === name));
    const selectedField = allowedFields.some(({name}) => name === field);

    function submit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault();
        const formData = new FormData(event.currentTarget);
        if (!(formData.get("worksheetName") as string).trim()) formData.delete("worksheetName");
        if (mappings.length) formData.set("fieldMappings", JSON.stringify(Object.fromEntries(mappings.map(({field, column}) => [field, column]))));
        void onUpload(formData, () => {
            formRef.current?.reset();
            setMappings([]);
            setField("");
            setColumn("");
        });
    }

    function addMapping() {
        if (!selectedField || !column.trim()) return;
        setMappings([...mappings, {field, column: column.trim()}]);
        setField("");
        setColumn("");
    }

    return <details className={styles.uploadDetails}>
        <summary>Import a survey</summary>
        <form ref={formRef} className={styles.uploadForm} encType="multipart/form-data" onSubmit={submit}>
            <label htmlFor="workbook-file">Workbook file</label>
            <input id="workbook-file" type="file" name="file" accept=".xlsx" required/>
            <label htmlFor="criteria-file">Selection criteria (optional, .json)</label>
            <input id="criteria-file" type="file" name="selectionCriteria" accept=".json,application/json"/>
            <label htmlFor="worksheet-name">Worksheet name (optional, first sheet by default)</label>
            <input id="worksheet-name" type="text" name="worksheetName" placeholder="Worksheet name"/>
            <fieldset className={styles.mappingEditor}>
                <legend>Field mappings (optional)</legend>
                <p>Map only fields whose column names differ from Mapwisefox.</p>
                <div className={styles.mappingPills}>
                    {mappings.map((mapping) => <span className={styles.mappingPill} key={mapping.field}>
                        {mapping.field}={mapping.column}
                        <button type="button" aria-label={`Remove ${mapping.field} mapping`} onClick={() => setMappings(mappings.filter(({field}) => field !== mapping.field))}>x</button>
                    </span>)}
                </div>
                <div className={styles.mappingInputs}>
                    {selectedField ? <span>{field}</span> : <><input aria-label="Mapwisefox field" list="supported-fields" value={field} onChange={(event) => setField(event.target.value)} placeholder="Field"/>
                        <datalist id="supported-fields">
                            {allowedFields.map(({name, mandatory}) => <option key={name} value={name}>{mandatory ? "mandatory" : "optional"}</option>)}
                        </datalist></>}
                    {selectedField && <><span aria-hidden="true">=</span><input aria-label="Workbook column" value={column} onChange={(event) => setColumn(event.target.value)} placeholder="Workbook column"/></>}
                    <button type="button" onClick={addMapping} disabled={!selectedField || !column.trim()}>Add mapping</button>
                </div>
            </fieldset>
            <input type="hidden" name="decisionColumn" value={config.decisionColumn}/>
            <input type="hidden" name="exclusionReasonColumn" value={config.exclusionReasonColumn}/>
            <button type="submit">Upload</button>
        </form>
    </details>;
}
