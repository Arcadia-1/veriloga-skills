from __future__ import annotations

from pathlib import Path

from veriloga.references.check_spectre_portability import ROOT, check_paths, scan_text


def test_flags_rigid_voltage_branch_triangle() -> None:
    text = """
module vco_bad(OUTP, OUTN, VSS);
analog begin
    V(OUTP, VSS) <+ vcm + vdiff;
    V(OUTN, VSS) <+ vcm - vdiff;
    V(OUTP, OUTN) <+ 2.0 * vdiff + noise_v;
end
endmodule
"""

    findings = scan_text(Path("vco_bad.va"), text)

    assert len(findings) == 1
    assert "OUTN, OUTP, VSS" in findings[0].message
    assert "rigid ideal voltage-branch triangle" in findings[0].message


def test_allows_two_voltage_branches_plus_current_injection() -> None:
    text = """
module vco_good(OUTP, OUTN, VSS);
analog begin
    V(OUTP, VSS) <+ outp_target;
    V(OUTN, VSS) <+ outn_target;
    I(OUTP, OUTN) <+ noise_i;
end
endmodule
"""

    assert scan_text(Path("vco_good.va"), text) == []


def test_ignores_commented_voltage_branches() -> None:
    text = """
module comments_only(A, B, C);
analog begin
    V(A, B) <+ vab;
    // V(A, C) <+ vac;
    /*
    V(B, C) <+ vbc;
    */
end
endmodule
"""

    assert scan_text(Path("comments_only.va"), text) == []


def test_flags_runtime_indexed_analog_bus_reads() -> None:
    text = """
module bad_bus(DIN, OUT);
integer i;
analog begin
    for (i = 0; i < 4; i = i + 1)
        if (V(DIN[i]) > vth) code = code + (1 << i);
end
endmodule
"""

    findings = scan_text(Path("bad_bus.va"), text)

    assert len(findings) == 1
    assert "runtime-indexed analog bus read V(DIN[i])" in findings[0].message


def test_allows_fixed_and_genvar_bus_indices() -> None:
    text = """
module good_bus(DIN, OUT);
genvar k;
genvar step;
analog begin
    if (V(DIN[0]) > vth) code = code + 1;
    if (V(DIN[`NUM_ADC_BITS-step+1]) > vth) code = code + 1;
    for (k = 0; k < 4; k = k + 1)
        V(OUT[k]) <+ transition(out_t[k], 0, tt, tt);
end
endmodule
"""

    assert scan_text(Path("good_bus.va"), text) == []


def test_repository_examples_are_free_of_rigid_branch_triangles() -> None:
    findings = check_paths([ROOT / "veriloga" / "assets"])

    assert not findings, "Spectre portability findings remain:\n" + "\n".join(
        finding.format() for finding in findings
    )
