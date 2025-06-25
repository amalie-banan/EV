import os
import pandas as pd
import matplotlib.pyplot as plt

class MissingWeatherDataAnalyzer:
    def __init__(self, df_wide: pd.DataFrame, plot_dir: str = "plots/plots_missing_data_weather"):
        self.df_original = df_wide.copy()
        self.plot_dir = plot_dir
        os.makedirs(self.plot_dir, exist_ok=True)

        # Kolonner vi er interesserede i
        self.columns = ['wind_speed', 'wind_dir', 'temp']

        # Opret flag for mangler
        self.df_original['missing_any'] = self.df_original[self.columns].isnull().any(axis=1)

        # Lav base sortering
        self.df_original = self.df_original.sort_values(by=['station_id', 'timestamp'])

    def run_all_methods(self):
        print("Running missing data handling methods...")

        methods = {
            "dropna": self._method_dropna,
            "interpolate": self._method_interpolate,
            "interpolate_then_median": self._method_interpolate_then_median,
        }

        summary = []

        for name, method in methods.items():
            df_result = method()
            missing_after = df_result[self.columns].isnull().any(axis=1).sum()
            summary.append({"method": name, "missing_after": missing_after})
            self._plot_sample_station(df_result, method_name=name)

        summary_df = pd.DataFrame(summary)
        summary_path = os.path.join(self.plot_dir, "summary.csv")
        summary_df.to_csv(summary_path, index=False)
        print(f"\n✅ Summary gemt i: {summary_path}\n")
        print(summary_df)
        return summary_df

    def _method_dropna(self):
        return self.df_original.dropna(subset=self.columns)

    def _method_interpolate(self):
        df = self.df_original.copy()
        df[self.columns] = df.groupby('station_id')[self.columns].transform(lambda g: g.interpolate())
        return df

    def _method_interpolate_then_median(self):
        df = self._method_interpolate()
        for col in self.columns:
            df[col] = df[col].fillna(df[col].median())
        return df

    def _plot_sample_station(self, df, method_name):
        sample_station = df['station_id'].mode()[0]  # Tag mest almindelige
        subset = df[df['station_id'] == sample_station].copy()

        for col in self.columns:
            plt.figure(figsize=(10, 4))
            plt.plot(subset['timestamp'], subset[col], label=col)
            plt.title(f"{col} - Station {sample_station} ({method_name})")
            plt.xlabel("Time")
            plt.ylabel(col)
            plt.grid(True)
            plt.tight_layout()

            fname = f"{method_name}_station{sample_station}_{col}.png"
            fpath = os.path.join(self.plot_dir, fname)
            plt.savefig(fpath)
            plt.close()
            print(f"Plot gemt: {fpath}")
