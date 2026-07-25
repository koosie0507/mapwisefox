import {useEffect, useState} from "react";
import {useParams, useSearchParams} from "react-router-dom";
import type {ScreeningResponse} from "../models/transfer.ts";
import EvidenceEditor from "./EvidenceEditor.tsx";
import {getScreening} from "../api.ts";

export default function EvidencePage() {
    const {fileName: encodedFileName = ""} = useParams();
    const [searchParams] = useSearchParams();
    const fileName = decodeURIComponent(encodedFileName);
    const indexValue = searchParams.get("index");
    const index = indexValue === null ? null : Number(indexValue);
    const validIndex = indexValue === null || (/^-?\d+$/.test(indexValue) && Number.isSafeInteger(index));
    const [screening, setScreening] = useState<ScreeningResponse | null>(null);
    const [error, setError] = useState(!validIndex);

    useEffect(() => {
        if (!validIndex) return;
        let active = true;
        const resource = `/api/v1/workbooks/${encodeURIComponent(fileName)}/screening`;

        void (async () => {
            const initialIndex = index ?? 0;
            let data = await getScreening(resource, initialIndex);
            if (index === null && data.firstUndecidedIndex !== null && data.firstUndecidedIndex !== initialIndex) {
                data = await getScreening(resource, data.firstUndecidedIndex);
            }
            if (active) setScreening(data);
        })().catch(() => {
            if (active) setError(true);
        });

        return () => {
            active = false;
        };
    }, [fileName, index, validIndex]);

    useEffect(() => {
        document.title = `ERSA-SMS Survey - ${fileName}`;
    }, [fileName]);

    if (error) return <p role="alert">Could not load that screening record.</p>;
    if (!screening) return null;
    return <EvidenceEditor evidence={screening.evidence} fileName={fileName}/>;
}
