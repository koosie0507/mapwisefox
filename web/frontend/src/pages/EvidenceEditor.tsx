import SelectionCriteriaForm from "../components/SelectionCriteriaForm";

type EvidenceProps = {
    evidenceId: number | string
    fileName: string
    include: boolean
    exclusionCriteria: Array<string>
};

export default function EvidenceEditor(props: EvidenceProps) {
  return (
    <SelectionCriteriaForm evidenceId={props.evidenceId} fileName={props.fileName} include={props.include} exclusionCriteria={props.exclusionCriteria} />
  );
}
