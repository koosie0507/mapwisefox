import {render, screen} from "@testing-library/react";
import {describe, expect, it} from "vitest";
import InclusionStatus from "./InclusionStatus.tsx";

describe("InclusionStatus", () => {
    it("renders include state", () => {
        render(<InclusionStatus include={true} excludeReasons={[]}/>);
        expect(screen.getByRole("button", {name: "Include"})).toBeInTheDocument();
    });

    it("renders exclusion reasons when present", () => {
        render(<InclusionStatus include={false} excludeReasons={["not software"]}/>);
        expect(screen.getByText("not software")).toBeInTheDocument();
    });

    it("hides reasons section when only blank reasons are present", () => {
        render(<InclusionStatus include="exclude" excludeReasons={[""]}/>);
        expect(screen.queryByText("Reasons:")).not.toBeInTheDocument();
    });

    it("renders empty reason placeholder when no reasons are provided", () => {
        render(<InclusionStatus include="exclude" excludeReasons={[]}/>);
        expect(screen.queryByText("Reasons:")).not.toBeInTheDocument();
    });
});
