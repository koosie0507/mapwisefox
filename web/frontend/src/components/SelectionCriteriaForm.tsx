import {type FormEvent, useEffect, useState} from "react";
import InclusionStatus from "./InclusionStatus.tsx";
import {type StatusChangedArgs, SelectionCriterion} from "./SelectionCriterion.tsx";
import "../styles/form.css";
import type {EvidenceViewModel} from "../models/viewmodel.ts";
import type {SelectionConfig} from "../models/transfer.ts";

export type IncludeStatusArgs = {
    include: boolean,
    excludeReasons: string[]
}

type SelectionCriteriaFormProps = {
    evidence: EvidenceViewModel
    fileName: string
    criteria: SelectionConfig | null
    onFormSubmit: (args: IncludeStatusArgs) => Promise<void>;
}

export function SelectionCriteriaForm({evidence, criteria, onFormSubmit}: SelectionCriteriaFormProps) {
    const [include, setInclude] = useState(evidence.include)
    const [excludeReasons, setExcludeReasons] = useState<string[]>(evidence.excludeReasons)

    useEffect(() => {
        setInclude(evidence.include);
        setExcludeReasons(evidence.excludeReasons ?? []);
    }, [evidence]);

    function manipulateExcludeReasons(include: boolean, excludeReason: string) {
        const buf = Object.assign([], excludeReasons);
        const idx = buf.indexOf(excludeReason)
        if (include) {
            if (idx >= 0) {
                buf.splice(idx, 1);
            }
        } else {
            if (idx < 0) {
                buf.push(excludeReason);
            }
        }
        setExcludeReasons(buf)
        setInclude(buf.length == 0)
    }

    async function handleIncludeStatusChanged({newValue, excludeReason}: StatusChangedArgs) {
        manipulateExcludeReasons(newValue, excludeReason);
    }

    async function submitData(evt: FormEvent<HTMLFormElement>) {
        evt.preventDefault();
        await onFormSubmit({include, excludeReasons});
    }

    return (
        <form className="criteria-form" onSubmit={submitData}>
            <InclusionStatus include={include} excludeReasons={excludeReasons} />
            {criteria && <>
                <h3>Inclusion Criteria</h3>
                <ul>
                    {criteria.inclusion_criteria.map((criterion, i) =>
                        <SelectionCriterion key={`include_${i}`} evidence={evidence} criterionId={`include_${i}`}
                                   criterionType="include"
                                   excludeReason={criterion.label}
                                   onStatusChanged={handleIncludeStatusChanged}>
                            {criterion.description}
                        </SelectionCriterion>
                    )}
                </ul>
                <h3>Exclusion Criteria</h3>
                <ul>
                    {criteria.exclusion_criteria.map((criterion, i) =>
                        <SelectionCriterion key={`exclude_${i}`} evidence={evidence} criterionId={`exclude_${i}`}
                                   criterionType="exclude"
                                   excludeReason={criterion.label}
                                   onStatusChanged={handleIncludeStatusChanged}>
                            {criterion.description}
                        </SelectionCriterion>
                    )}
                </ul>
            </>}
        </form>
    )
}