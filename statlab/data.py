"""Loading the run results and the GSCDB137 reference tables."""
from __future__ import annotations

import collections
import glob
import json
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RUN = ROOT / "gscdb_results" / "applied_def2-tzvpp_scf"
GSCDB = ROOT / "GSCDB-main"

HARTREE2KCAL = 627.509474
R2 = "r2SCAN"
NN = "NN-r2SCAN"
DATATYPES = ["BH", "TC", "ISO", "INC", "NC"]
DATATYPE_NAMES = {
    "BH": "Barrier Height",
    "TC": "Thermochemistry",
    "ISO": "Isomerization",
    "INC": "Intramolecular Noncovalent",
    "NC": "Noncovalent",
}


@lru_cache
def summary() -> dict:
    return json.loads((RUN / "analysis" / "summary.json").read_text())


def training_overlap() -> list[str]:
    """Reactions built only from molecules seen in NN training (data leakage)."""
    return list(summary()["training_overlap"])


def load_reactions(drop_overlap: bool = True) -> pd.DataFrame:
    """One row per reaction: reference, both methods, signed errors (kcal/mol).

    Columns: rxn, ds, dt, ref, E_r2, E_nn, e_r2, e_nn, se (GSCDB standard error
    of the set), z_r2, z_nn (errors in units of se), delta = |e_nn| - |e_r2|.
    """
    df = pd.read_csv(RUN / "analysis" / "per_reaction.csv")
    df.columns = ["rxn", "ds", "ref", "E_r2", "E_nn", "e_r2", "e_nn"]
    st = summary()["stats"]
    df["dt"] = df.ds.map({k: v["datatype"] for k, v in st.items()})
    df["se"] = df.ds.map({k: v["standard_error"] for k, v in st.items()})
    if drop_overlap:
        df = df[~df.rxn.isin(training_overlap())]
    df["z_r2"] = df.e_r2 / df.se
    df["z_nn"] = df.e_nn / df.se
    df["delta"] = df.e_nn.abs() - df.e_r2.abs()
    df["dt"] = pd.Categorical(df.dt, DATATYPES)
    return df.reset_index(drop=True)


def _composition(xyz: str) -> collections.Counter:
    return collections.Counter(line.split()[0] for line in xyz.strip().splitlines())


@lru_cache
def _allmols() -> dict:
    return json.loads((GSCDB / "Allmols_info.json").read_text())


def load_molecules() -> pd.DataFrame:
    """One row per molecule: total energies of both methods, timings, composition.

    dE = E_nn - E_r2 in kcal/mol; n_<El> columns hold element counts.
    """
    allmols = _allmols()
    rows = []
    for f in sorted(glob.glob(str(RUN / "energies_shard*.jsonl"))):
        for line in open(f):
            r = json.loads(line)
            (e_r2, e_nn), (t_r2, t_nn) = r["energies"].values(), r["timings"].values()
            comp = _composition(allmols[r["molecule"]]["molecule"])
            rows.append(dict(
                mol=r["molecule"], natm=r["natm"], nao=r["nao"],
                charge=r["charge"], spin=r["spin"],
                E_r2=e_r2, E_nn=e_nn, dE=(e_nn - e_r2) * HARTREE2KCAL,
                t_r2=t_r2, t_nn=t_nn,
                **{f"n_{el}": n for el, n in comp.items()},
            ))
    df = pd.DataFrame(rows)
    el = element_columns(df)
    df[el] = df[el].fillna(0).astype(int)
    df["shell"] = np.where(df.spin > 0, "open", "closed")
    return df


def element_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith("n_")]


def stoichiometry() -> dict[str, list[tuple[float, str]]]:
    """Reaction -> [(coefficient, molecule), ...] from GSCDB DatasetEval.csv."""
    ev = pd.read_csv(GSCDB / "Info" / "DatasetEval.csv")
    out = {}
    for rxn, s in zip(ev.Reaction, ev.Stoichiometry):
        tok = s.split(",")
        out[rxn] = [(float(tok[i]), tok[i + 1]) for i in range(0, len(tok), 2)]
    return out


def reaction_descriptors(rxn: pd.DataFrame, mol: pd.DataFrame) -> pd.DataFrame:
    """Simple structural descriptors of each reaction (no quantum chemistry)."""
    st = stoichiometry()
    natm = mol.set_index("mol").natm
    spin = mol.set_index("mol").spin
    rows = []
    for r in rxn.rxn:
        terms = st[r]
        rows.append(dict(
            rxn=r,
            n_species=len(terms),
            atoms_moved=sum(abs(c) * natm[m] for c, m in terms),
            max_natm=max(natm[m] for _, m in terms),
            open_shell=int(any(spin[m] > 0 for _, m in terms)),
        ))
    return pd.DataFrame(rows)


def load_gscdb_population(datasets) -> pd.DataFrame:
    """Full GSCDB137 reactions of the given sets with errors of published DFAs."""
    df = pd.read_csv(GSCDB / "Analysis" / "Results_errors.csv")
    ds = pd.read_csv(GSCDB / "Info" / "Datasets.csv")[["Name", "Datatype_Short"]]
    df = df[df.Dataset.isin(set(datasets))]
    df = df.merge(ds, left_on="Dataset", right_on="Name", how="left")
    return df.rename(columns={"Datatype_Short": "dt"}).drop(columns="Name")
