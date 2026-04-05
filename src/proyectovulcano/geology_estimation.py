from __future__ import annotations

import numpy as np
import pandas as pd


class DrillholeDataManager:
    """Gestión y validación de datos de barrenos, litológicos, analíticos."""

    REQUIRED_COLUMNS = ["hole_id", "x", "y", "z"]

    def __init__(self, df: pd.DataFrame):
        """Initialize with drillhole dataframe."""
        self.df = df
        self.validation_result = self.validate_columns()

    def validate_columns(self) -> dict:
        """Validate presence of required columns."""
        missing = [col for col in self.REQUIRED_COLUMNS
                   if col not in self.df.columns]
        return {
            "missing": missing,
            "valid": len(missing) == 0,
            "total_holes": self.df["hole_id"].nunique() if "hole_id" in self.df.columns else 0,
            "total_samples": len(self.df),
        }

    def filter_by_lithology(self, lith_col: str,
                           values: list[str]) -> pd.DataFrame:
        """Filter by lithology (if column exists)."""
        if lith_col not in self.df.columns:
            return self.df.copy()
        mask = self.df[lith_col].isin(values)
        return self.df[mask].copy()

    def filter_by_geophysics(self, geo_col: str,
                            values: list[str]) -> pd.DataFrame:
        """Filter by geophysical response (if column exists)."""
        if geo_col not in self.df.columns:
            return self.df.copy()
        mask = self.df[geo_col].isin(values)
        return self.df[mask].copy()

    def filter_by_analytics(self, anal_col: str,
                           values: list[str]) -> pd.DataFrame:
        """Filter by analytical category (if column exists)."""
        if anal_col not in self.df.columns:
            return self.df.copy()
        mask = self.df[anal_col].isin(values)
        return self.df[mask].copy()

    def summary(self) -> dict:
        """Return summary statistics of drillhole dataset."""
        summary = {
            "holes": self.df["hole_id"].nunique() if "hole_id" in self.df.columns else 0,
            "samples": len(self.df),
        }
        
        # Add lithology summary if column exists
        if "lith" in self.df.columns:
            summary["lithologies"] = int(self.df["lith"].nunique())
            summary["lith_types"] = list(self.df["lith"].unique())
        
        # Add geophysics summary if column exists
        if "geo" in self.df.columns:
            summary["geophysics"] = int(self.df["geo"].nunique())
            summary["geo_types"] = list(self.df["geo"].unique())
        
        # Add analytics summary if column exists
        if "anal" in self.df.columns:
            summary["analytics"] = int(self.df["anal"].nunique())
            summary["anal_types"] = list(self.df["anal"].unique())
        
        return summary

    def get_statistics(self, numeric_cols: list[str] | None = None) -> dict:
        """Get statistics for numeric columns."""
        if numeric_cols is None:
            numeric_cols = self.df.select_dtypes(include=[np.number]).columns.tolist()
        
        stats = {}
        for col in numeric_cols:
            if col in self.df.columns:
                stats[col] = {
                    "mean": float(self.df[col].mean()),
                    "median": float(self.df[col].median()),
                    "std": float(self.df[col].std()),
                    "min": float(self.df[col].min()),
                    "max": float(self.df[col].max()),
                }
        return stats


class CompositingTools:
    """Advanced compositing methods for drillhole data."""

    @staticmethod
    def composite_by_length(df: pd.DataFrame, length: float,
                           value_col: str) -> pd.DataFrame:
        """Create fixed-length composites from drillhole samples."""
        if length <= 0:
            raise ValueError("Length must be > 0")
        if value_col not in df.columns:
            raise ValueError(f"Column not found: {value_col}")

        composites: list[dict] = []
        
        for hole_id, group in df.groupby("hole_id", sort=False):
            ordered = group.sort_values("z", ascending=False).copy()
            ordered[value_col] = pd.to_numeric(ordered[value_col], errors="coerce")
            ordered = ordered.dropna(subset=[value_col])
            
            if ordered.empty:
                continue
            
            # Calculate cumulative depth
            coords = ordered[["x", "y", "z"]].to_numpy()
            if len(coords) > 0:
                deltas = np.linalg.norm(np.diff(coords, axis=0), axis=1)
                depth = np.concatenate([[0.0], np.cumsum(deltas)])
                comp_idx = np.floor(depth / length).astype(int)
                
                for idx in np.unique(comp_idx):
                    mask = comp_idx == idx
                    comp_df = ordered[mask].copy()
                    
                    composites.append({
                        "hole_id": hole_id,
                        "comp_from": float(idx * length),
                        "comp_to": float((idx + 1) * length),
                        "x": float(comp_df["x"].mean()),
                        "y": float(comp_df["y"].mean()),
                        "z": float(comp_df["z"].mean()),
                        value_col: float(comp_df[value_col].mean()),
                        "n_samples": int(len(comp_df)),
                    })
        
        if not composites:
            return pd.DataFrame()
        return pd.DataFrame(composites)

    @staticmethod
    def plan_infill_drillholes(df: pd.DataFrame,
                              min_spacing: float) -> pd.DataFrame:
        """Plan infill drillholes to achieve minimum spacing."""
        if min_spacing <= 0:
            raise ValueError("Minimum spacing must be > 0")
        
        coords = df[["x", "y", "z"]].to_numpy()
        planned = []
        
        for i in range(len(coords) - 1):
            dist = np.linalg.norm(coords[i+1] - coords[i])
            if dist > min_spacing:
                mid = (coords[i] + coords[i+1]) / 2.0
                planned.append({
                    "x": float(mid[0]),
                    "y": float(mid[1]),
                    "z": float(mid[2]),
                    "spacing": float(dist),
                })
        
        return pd.DataFrame(planned) if planned else pd.DataFrame()


class StratigraphicModeler:
    """Explicit and implicit stratigraphic modeling."""

    @staticmethod
    def explicit_model(df: pd.DataFrame, domain_col: str) -> pd.DataFrame:
        """Create explicit stratigraphic model by domain."""
        if domain_col not in df.columns:
            raise ValueError(f"Domain column not found: {domain_col}")
        
        # Calculate centroid for each domain
        centroids = df.groupby(domain_col, as_index=False)[["x", "y", "z"]].mean()
        centroids = centroids.rename(columns={"z": "elevation"})
        
        return centroids

    @staticmethod
    def compute_domain_contacts(df: pd.DataFrame, domain_col: str,
                               depth_col: str = "z") -> pd.DataFrame:
        """Identify domain contact points along drillholes."""
        if domain_col not in df.columns:
            raise ValueError(f"Domain column not found: {domain_col}")
        
        contacts: list[dict] = []
        
        for hole_id, hole_df in df.groupby("hole_id", sort=False):
            hole_df = hole_df.sort_values(depth_col, ascending=False).copy()
            domains = hole_df[domain_col].values
            depths = hole_df[depth_col].values
            coords = hole_df[["x", "y"]].values
            
            for i in range(len(domains) - 1):
                if domains[i] != domains[i+1]:
                    # Interpolate contact position
                    contact_depth = (depths[i] + depths[i+1]) / 2.0
                    contact_x = (coords[i][0] + coords[i+1][0]) / 2.0
                    contact_y = (coords[i][1] + coords[i+1][1]) / 2.0
                    
                    contacts.append({
                        "hole_id": hole_id,
                        "x": float(contact_x),
                        "y": float(contact_y),
                        "z": float(contact_depth),
                        "domain_from": str(domains[i]),
                        "domain_to": str(domains[i+1]),
                    })
        
        return pd.DataFrame(contacts) if contacts else pd.DataFrame()

# Métodos de estimación de leyes
class EstimationMethods:
    @staticmethod
    def idw(df: pd.DataFrame, x: float, y: float, z: float, value_col: str, power=2) -> float:
        dists = np.sqrt((df["x"]-x)**2 + (df["y"]-y)**2 + (df["z"]-z)**2)
        vals = df[value_col]
        weights = 1/(dists**power+1e-6)
        return np.sum(vals*weights)/np.sum(weights)

    @staticmethod
    def simple_kriging(df: pd.DataFrame, x: float, y: float, z: float, value_col: str) -> float:
        # Implementación básica: media global + ruido
        mean = df[value_col].mean()
        return mean + np.random.normal(0, df[value_col].std()/10)

    @staticmethod
    def ordinary_kriging(df: pd.DataFrame, x: float, y: float, z: float, value_col: str) -> float:
        # Implementación básica: media local (vecinos)
        dists = np.sqrt((df["x"]-x)**2 + (df["y"]-y)**2 + (df["z"]-z)**2)
        mask = dists < 30
        vals = df.loc[mask, value_col]
        return vals.mean() if not vals.empty else df[value_col].mean()

    @staticmethod
    def indicator_kriging(df: pd.DataFrame, x: float, y: float, z: float, value_col: str, threshold: float) -> float:
        dists = np.sqrt((df["x"]-x)**2 + (df["y"]-y)**2 + (df["z"]-z)**2)
        mask = dists < 30
        vals = df.loc[mask, value_col]
        return (vals > threshold).mean() if not vals.empty else (df[value_col] > threshold).mean()

    @staticmethod
    def indicator_simulation(df: pd.DataFrame, value_col: str, n_realizations=10) -> np.ndarray:
        # Simulación: bootstrapping
        return np.random.choice(df[value_col], size=n_realizations, replace=True)

# Herramientas de análisis y modelado de variogramas
class VariogramAnalyzer:
    @staticmethod
    def experimental_variogram(df: pd.DataFrame, value_col: str, lag: float, n_lags: int) -> pd.DataFrame:
        semivariances = []
        for i in range(1, n_lags+1):
            h = lag * i
            pairs = []
            for idx1, row1 in df.iterrows():
                for idx2, row2 in df.iterrows():
                    dist = np.sqrt((row1["x"]-row2["x"])**2 + (row1["y"]-row2["y"])**2 + (row1["z"]-row2["z"])**2)
                    if abs(dist-h) < lag/2:
                        pairs.append((row1[value_col], row2[value_col]))
            if pairs:
                gamma = 0.5 * np.mean([(a-b)**2 for a,b in pairs])
                semivariances.append({"lag": h, "gamma": gamma})
        return pd.DataFrame(semivariances)

    @staticmethod
    def plot_variogram(variogram_df: pd.DataFrame, filename: str) -> None:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(variogram_df["lag"], variogram_df["gamma"], marker="o")
        plt.xlabel("Lag")
        plt.ylabel("Semivarianza")
        plt.title("Variograma experimental")
        plt.savefig(filename)

# Herramientas de análisis de datos
class DataAnalysisTools:
    @staticmethod
    def strip_diagram(df: pd.DataFrame, value_col: str) -> pd.DataFrame:
        return df[["z", value_col]].sort_values("z")

    @staticmethod
    def contact_profile(df: pd.DataFrame, domain_col: str, value_col: str) -> pd.DataFrame:
        return df.groupby(domain_col)[value_col].mean().reset_index()

    @staticmethod
    def data_spacing(df: pd.DataFrame) -> float:
        coords = df[["x", "y", "z"]].to_numpy()
        dists = [np.linalg.norm(coords[i]-coords[i+1]) for i in range(len(coords)-1)]
        return np.mean(dists) if dists else 0.0

    @staticmethod
    def capping_analysis(df: pd.DataFrame, value_col: str, cap: float) -> pd.DataFrame:
        capped = df[value_col].clip(upper=cap)
        stats = capped.describe()
        return stats

    @staticmethod
    def plot_strip_diagram(df: pd.DataFrame, value_col: str, filename: str) -> None:
        import matplotlib.pyplot as plt
        plt.figure()
        plt.plot(df["z"], df[value_col], marker=".")
        plt.xlabel("Profundidad (z)")
        plt.ylabel(value_col)
        plt.title("Diagrama de franja")
        plt.savefig(filename)

# Herramientas de exportación
class ReportExporter:
    @staticmethod
    def export_plot(df: pd.DataFrame, filename: str) -> None:
        import matplotlib.pyplot as plt
        plt.figure()
        df.plot()
        plt.savefig(filename)

    @staticmethod
    def export_report(text: str, filename: str) -> None:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(text + "\n")

    @staticmethod
    def export_dataframe(df: pd.DataFrame, filename: str) -> None:
        df.to_csv(filename, index=False)

# Herramientas de lavabilidad del carbón
class CoalWashabilityTools:
    @staticmethod
    def analyze(df: pd.DataFrame, coal_col: str) -> dict:
        # Simplificado: proporción de muestras lavables
        lavable = df[coal_col] > 0.5 if coal_col in df.columns else pd.Series([])
        return {"lavable": lavable.mean() if not lavable.empty else None}

# Escultura geológica interactiva 3D
class InteractiveGeologicalSculpture:
    @staticmethod
    def sculpt(df: pd.DataFrame, mask_col: str) -> pd.DataFrame:
        # Simplificado: filtra puntos para "escultura"
        if mask_col not in df.columns:
            return df
        return df[df[mask_col] == 1]

# Herramientas de manipulación de fallas
class FaultTools:
    @staticmethod
    def detect_faults(df: pd.DataFrame, value_col: str, threshold: float) -> pd.DataFrame:
        # Detecta saltos bruscos en la variable
        diffs = df[value_col].diff().abs()
        faults = df[diffs > threshold]
        return faults
