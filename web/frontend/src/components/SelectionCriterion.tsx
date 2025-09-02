
import React from "react";

export type SelectionCriterionProps = {
  children: React.ReactNode;
  fileName: string;
  evidenceId: number | string;
  criterionId: string;
  criterionType: "include" | "exclude";
  excludeReason: string;
  exclusionCriteria: string[];
  onToggleCompleted: (payload: {
    status: "include" | "exclude" | boolean;
    remainingExclusions: string[];
  }) => void;
};

const TOGGLE_EXCLUDE_REASON_ENDPOINT: string = "/toggle-exclude-reason"

export default function SelectionCriterion({
    children,
    fileName,
    evidenceId,
    criterionId,
    criterionType,
    excludeReason,
    onToggleCompleted,
    exclusionCriteria,
}: SelectionCriterionProps) {
    const [checked, setChecked] = React.useState(
        (
            (criterionType === "exclude" && exclusionCriteria.includes(excludeReason))
            ||
            (criterionType === "include" && !exclusionCriteria.includes(excludeReason))
        )
    )
    const handleChange: React.ChangeEventHandler<HTMLInputElement> = (evt) => {
        const newValue = evt.target.checked;
        fetch(`/evidence/${fileName}${TOGGLE_EXCLUDE_REASON_ENDPOINT}`, {
            method: 'PATCH',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                id: Number(evidenceId),
                toggle: (criterionType === "exclude") ? newValue : !newValue,
                exclude_reason: excludeReason
            })
        }).then(res => {
            res.json().then(data => {
                onToggleCompleted({
                    status: data.selection_status,
                    remainingExclusions: data.remaining_exclusions
                })
            }).catch(err => console.error(err));
            setChecked(newValue);
        }).catch(err => {
            console.error("Failed to send update:", err);
        });
    }
    return (
        <li>
            <input type="checkbox"
                   id={criterionId}
                // the default state is to include
                   checked={checked}
                   onChange={handleChange}
            />
            <label className={criterionType} htmlFor={criterionId}>{children}</label>
        </li>
    )
}