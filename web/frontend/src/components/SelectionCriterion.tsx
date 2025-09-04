import React, {type ChangeEvent, useCallback, useEffect} from "react";
import type {EvidenceViewModel} from "../models/viewmodel.ts";

export type StatusChangedArgs = {
    oldValue: boolean,
    newValue: boolean,
    excludeReason: string
}

export type SelectionCriterionProps = {
    children: React.ReactNode;
    criterionId: string;
    criterionType: "include" | "exclude";
    evidence: EvidenceViewModel;
    excludeReason: string;
    onStatusChanged: (data: StatusChangedArgs) => Promise<void>;
};

export function SelectionCriterion(props: SelectionCriterionProps) {
    const {
        children, criterionId, criterionType, evidence, excludeReason, onStatusChanged,
    } = props;

    const isInitiallyChecked = useCallback(() => {
        const isExcludeReason = evidence.excludeReasons.includes(excludeReason);
        return (criterionType === "exclude" && isExcludeReason
            || criterionType === "include" && !isExcludeReason);
    }, [evidence, excludeReason, criterionType]);
    const [checked, setChecked] = React.useState(isInitiallyChecked())
    useEffect(() => {setChecked(isInitiallyChecked())}, [isInitiallyChecked]);

    function shouldInclude(isChecked: boolean) {
        return criterionType === "exclude" && !isChecked || criterionType === "include" && isChecked
    }

    async function handleChanged(evt: ChangeEvent<HTMLInputElement>) {
        const newValue = shouldInclude(evt.target.checked);
        setChecked(evt.target.checked);
        await onStatusChanged({oldValue: !newValue, newValue, excludeReason});
    }

    return (
        <li>
            <input type="checkbox" id={criterionId} checked={checked} onChange={handleChanged}/>
            <label className={criterionType} htmlFor={criterionId}>{children}</label>
        </li>
    )
}