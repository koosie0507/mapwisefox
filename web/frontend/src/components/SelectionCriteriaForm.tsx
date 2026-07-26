import {type FormEvent, useEffect, useState} from "react";
import InclusionStatus from "./InclusionStatus.tsx";
import {type StatusChangedArgs, SelectionCriterion} from "./SelectionCriterion.tsx";
import "../styles/form.css";
import type {EvidenceViewModel} from "../models/viewmodel.ts";
import type {SelectionConfig} from "../models/transfer.ts";

const defaultCriteria: SelectionConfig = {
    review_topic: "",
    additional_context: null,
    inclusion_criteria: [{label: "", description: "study meets selection criteria"}],
    exclusion_criteria: [],
};

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
    const effectiveCriteria = criteria ?? defaultCriteria;
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
            <h3>Inclusion Criteria</h3>
            <ul>
                {effectiveCriteria.inclusion_criteria.map((criterion, i) =>
                    <SelectionCriterion key={`include_${i}`} evidence={evidence} criterionId={`include_${i}`}
                               criterionType="include"
                               excludeReason={criterion.label}
                               onStatusChanged={handleIncludeStatusChanged}>
                        {criterion.description}
                    </SelectionCriterion>
                )}
            </ul>
            {effectiveCriteria.exclusion_criteria.length > 0 && <>
                <h3>Exclusion Criteria</h3>
                <ul>
                    {effectiveCriteria.exclusion_criteria.map((criterion, i) =>
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