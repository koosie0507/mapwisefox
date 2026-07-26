import {type IncludeStatusArgs, SelectionCriteriaForm} from "../components/SelectionCriteriaForm";
import React, {useEffect, useRef, useState} from "react";
import {ChevronLeft, ChevronRight, CircleDashed, FastForward, SkipBack, SkipForward} from "lucide-react";
import styles from "./EvidenceEditor.module.css";
import type {NavigationAction, ScreeningResponse} from "../models/transfer.ts";
import type {EvidenceViewModel} from "../models/viewmodel.ts";
import {getScreening, updateScreening} from "../api.ts";

type EvidenceProps = {
    evidence: EvidenceViewModel
    fileName: string
};

function safeUrl(url?: string): string {
    return url || "#"
}

function SafeLink({url, text, label, style}: {
    url?: string,
    text?: string,
    label?: string,
    style?: React.CSSProperties
}) {
    if (label !== undefined && label !== null) {
        const spanStyle = style || {fontSize: "9px", margin: "2px"}
        return <span style={spanStyle}><b>{label}</b>&nbsp;<a href={safeUrl(url)} target="_blank">{text}</a></span>
    }
    return <a href={safeUrl(url)} target="_blank">{text}</a>;
}

async function fetchScreening(resource: string, index: number): Promise<ScreeningResponse | null> {
    try {
        return await getScreening(resource, index);
    } catch {
        return null;
    }
}

export default function EvidenceEditor({evidence, fileName}: EvidenceProps) {
    const [model, setModel] = useState<EvidenceViewModel>(evidence)
    const [screening, setScreening] = useState<ScreeningResponse | null>(null)
    const [error, setError] = useState<string | null>(null)
    const gotoInputRef = useRef<HTMLInputElement>(null);
    const resource = `/api/v1/workbooks/${encodeURIComponent(fileName)}/screening`;
    const doiText = model.doi || "n/a"
    const dateText = (model.publishedAt || "n/a").toString()

    useEffect(() => {
        void fetchScreening(resource, Number(evidence.clusterId)).then(data => {
            if (data) {
                setScreening(data)
                setModel(data.evidence)
            }
        })
    }, [evidence.clusterId, resource])

    async function load(index: number) {
        const data = await fetchScreening(resource, index)
        if (!data) {
            setError("Could not load that screening record.")
            return;
        }
        setScreening(data)
        setModel(data.evidence)
        setError(null)
    }

    async function navigate(value: string | number, action: NavigationAction) {
        const current = screening?.recordIndex ?? Number(model.clusterId)
        const count = screening?.recordCount
        const destinations: Partial<Record<NavigationAction, number | null>> = {
            first: 0,
            firstUnfilled: screening?.firstUndecidedIndex,
            prev: screening?.previousIndex ?? current - 1,
            next: screening?.nextIndex ?? current + 1,
            last: count === undefined ? current : count - 1,
            unfilled: screening?.nextUndecidedIndex ?? screening?.firstUndecidedIndex,
            goto: Number(value),
        }
        const destination = destinations[action]
        if (destination !== null && destination !== undefined && Number.isInteger(destination) && destination >= 0) {
            await load(destination)
        }
    }

    async function toggleStatus({include, excludeReasons}: IncludeStatusArgs) {
        const decision = include ? "included" : "excluded";
        try {
            const data = await updateScreening(resource, model.clusterId, decision, excludeReasons);
            setScreening(data)
            setModel(data.evidence)
            setError(null)
            const destination = data.nextUndecidedIndex ?? data.nextIndex
            if (destination !== null) await load(destination)
        } catch {
            setError("Could not save the screening decision.")
        }
    }

    return (
        <div className={styles.layout}>
            <main className={styles.mainContent}>
                {error && <p role="alert">{error}</p>}
                <h1>[{model.clusterId}]&nbsp;{model.title}</h1>
                <div className="article-info">
                    <div className="source-container">
                        <SafeLink url={model.url} text={model.publicationVenue} label="Source:"
                                  style={{fontSize: "12px", margin: "2px"}}/>
                        <SafeLink url={model.doiLink} text={doiText} label="DOI:"/>
                        <SafeLink url={model.sciHubLink} text={doiText} label="SciHub:"/>
                    </div>
                    <small style={{fontSize: "9px", margin: "2px"}}><b>Date Published:</b>&nbsp;{dateText}</small>
                </div>
                <b className="abstract-label">Abstract</b>
                <div className={styles.scrollbox}>{model.abstract}</div>
                <p className="keywords"><strong>Keywords:</strong>{model.keywords.join(", ")}</p>
            </main>
            <aside className={`${styles.rightSidebar} sidebar`}>
                <SelectionCriteriaForm evidence={model} fileName={fileName} criteria={screening?.selectionCriteria ?? null} onFormSubmit={toggleStatus}/>
            </aside>
            <footer className={styles.bottomPanel}>
                <div className={styles.buttonBar}>
                    <form method="post" action="" onSubmit={evt => evt.preventDefault()}>
                        <div className={styles.gotoGroup}>
                            <input type="number" min="0" ref={gotoInputRef} placeholder="Go to..." title="Enter an index to go to"
                                   className={styles.gotoInput} onKeyDown={async e => {
                                if (e.key === "Enter") {
                                    e.preventDefault();
                                    const value = gotoInputRef.current?.value?.trim();
                                    if (value) await navigate(value, "goto");
                                }
                            }}/>
                            <button type="submit" title="Go to item" className={styles.gotoBtn} onClick={async () => {
                                const value = gotoInputRef.current?.value?.trim();
                                if (value) await navigate(value, "goto");
                            }}><ChevronRight size={18}/></button>
                        </div>
                        <div className={styles.navGroup}>
                            <button type="submit" title="First item" onClick={() => navigate(0, "first")}><SkipBack size={18}/></button>
                            <button type="submit" title="Previous item" onClick={() => navigate(0, "prev")}><ChevronLeft size={18}/></button>
                            <button type="submit" title="Next item" onClick={() => navigate(0, "next")}><ChevronRight size={18}/></button>
                            <button type="submit" title="Last item" onClick={() => navigate(0, "last")}><SkipForward size={18}/></button>
                            <button type="submit" title="First undecided item" className={styles.firstGap}
                                    onClick={() => navigate(0, "firstUnfilled")}><CircleDashed size={18}/></button>
                            <button type="submit" title="Next undecided item" className={styles.nextUndecided}
                                    onClick={() => navigate(0, "unfilled")}><FastForward size={18}/></button>
                        </div>
                    </form>
                </div>
            </footer>
        </div>
    )
}
