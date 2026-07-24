import {useEffect, useState} from "react";
import type {ScreeningResponse} from "../models/transfer.ts";
import EvidenceEditor from "./EvidenceEditor.tsx";
import {apiFetch} from "../apiClient.ts";

export default function EvidencePage() {
    const filenamePart = window.location.pathname.match(/^\/evidence\/([^/]+)$/)?.[1] ?? "";
    const fileName = decodeURIComponent(filenamePart);
    const indexValue = new URLSearchParams(window.location.search).get("index");
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
            const initialResponse = await apiFetch(`${resource}/${initialIndex}`);
            if (!initialResponse.ok) {
                if (active) setError(true);
                return;
            }
            let data = await initialResponse.json() as ScreeningResponse;
            if (index === null && data.firstUndecidedIndex !== null && data.firstUndecidedIndex !== initialIndex) {
                const undecidedResponse = await apiFetch(`${resource}/${data.firstUndecidedIndex}`);
                if (!undecidedResponse.ok) {
                    if (active) setError(true);
                    return;
                }
                data = await undecidedResponse.json() as ScreeningResponse;
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
