"""Fact-check locks: slide text must match FACTCHECK.md corrections.
These tests pin the post-audit facts so future edits can't regress to
Conte's compressed (inaccurate) telling. See FACTCHECK.md for sources."""

import re


def all_text(slides):
    return re.sub(r"\s+", " ", " ".join(s.get_text(" ") for s in slides))


class TestCorrectedFacts:
    def test_petrillo_ban_is_1942_not_1930s(self, slides):
        text = all_text(slides)
        assert "1942" in text
        # The timeline must not place the ban in the 1930s
        assert not re.search(r"1930s.*?Petrillo", text, re.I), (
            "Petrillo's national ban was 1942–44, not the 1930s (FACTCHECK #2)"
        )

    def test_union_banned_synth_is_moog_not_novachord(self, slides):
        text = all_text(slides)
        assert "Moog" in text, "the banned synth was the Moog (1969)"
        assert not re.search(r"Novachord[^.]*ban", text, re.I), (
            "the Novachord was never banned — that was the Moog (FACTCHECK #3)"
        )

    def test_musician_count_is_20k(self, slides):
        text = all_text(slides)
        assert "20,000" in text or "~20K" in text
        assert "22,000" not in text and ">22K<" not in text, (
            "canonical AFM figure is ~20,000 within two years (FACTCHECK #1)"
        )

    def test_orchestra_crisis_attributions(self, slides):
        text = all_text(slides)
        assert "1992" in text and "Wolf" in text, "cite the 1992 ASOL/Wolf report"
        assert "Flanagan" in text, "the deficit research is Flanagan (2012)"
        assert "46 of the 63" not in text, "46/63 unverified — dropped (FACTCHECK #7)"
        assert "2008 Stanford GSB study" not in text

    def test_karen_x_cheng_attribution(self, slides):
        text = all_text(slides)
        assert "Karen X. Cheng" in text
        assert "Kerrydax" not in text and "Keredex" not in text, (
            "auto-caption garble — the creator is Karen X. Cheng (FACTCHECK #9)"
        )

    def test_fireship_beat_present(self, slides):
        text = all_text(slides)
        assert "The moat was coding itself" in text
        assert "Fireship" in text, "Fireship beat must carry attribution"

    def test_cpu_framing_intact(self, slides):
        text = all_text(slides)
        for phrase in (
            "CODE-PUPPY", "UNIVERSITY", "Puppy OS", "two halves of the same future",
            "The New Medium", "Agentic Craft for Creatives",
            "Creative Direction for Engineers", "The Rebuild Practice",
            "Ethics, Consent & Credit",
        ):
            assert phrase in text, f"locked CPU framing missing: {phrase}"


class TestActCoverage:
    def test_act_eyebrows_present(self, slides):
        text = all_text(slides)
        for act in ("Act I", "Act II", "Act III", "Act IV", "Act V", "Act VI", "Act VII", "Act VIII"):
            assert act in text, f"missing {act} marker"
