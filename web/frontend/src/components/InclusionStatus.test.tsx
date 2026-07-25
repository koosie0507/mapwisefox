import {render, screen} from "@testing-library/react";
import {describe, expect, it} from "vitest";
import InclusionStatus from "./InclusionStatus.tsx";

describe("InclusionStatus", () => {
    it("renders include state", () => {
        render(<InclusionStatus include={true} excludeReasons={[]}/>);
        expect(screen.getByRole("button", {name: "Include"})).toBeInTheDocument();
    });

    it("renders exclusion reasons and empty reason state", () => {
        const {rerender} = render(<InclusionStatus include={false} excludeReasons={["not software"]}/>);
        expect(screen.getByText("not software")).toBeInTheDocument();
        rerender(<InclusionStatus include="exclude" excludeReasons={[]}/>);
        expect(screen.getByText("-")).toBeInTheDocument();
    });
});
