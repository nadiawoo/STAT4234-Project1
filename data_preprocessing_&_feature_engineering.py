# -*- coding: utf-8 -*-
"""Data Preprocessing & Feature Engineering.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nhx65W4mTponIy1mz2u9cds_eFoRplGA
"""

from google.colab import files
uploaded = files.upload()

# Converting into a data frame
import pandas as pd

df = pd.read_csv("spotify_df_merged.csv")

# Checking data structure
print(df.head())

# FROM ASHLEY'S PRIOR WORK

import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler, StandardScaler, PowerTransformer
import math
import matplotlib.pyplot as plt
import seaborn as sns

x = df.head()
x

x.to_csv("head.csv", index = False)

# Calculate summary statistics for numerical columns
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
summary_stats = df[num_cols].describe().T

# Display the summary statistics
summary_stats

# Ensure numerical columns are selected
num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
num_plots = len(num_cols)
plots_per_figure = 9
num_figures = math.ceil(num_plots / plots_per_figure)
for fig_num in range(num_figures):
    fig, axes = plt.subplots(3, 3, figsize=(15, 10))
    axes = axes.flatten()

    start_idx = fig_num * plots_per_figure
    end_idx = min(start_idx + plots_per_figure, num_plots)

    for i, col in enumerate(num_cols[start_idx:end_idx]):
        sns.histplot(df[col], kde=True, bins=30, ax=axes[i])
        axes[i].set_title(f"Distribution of {col}")

    for j in range(i + 1, len(axes)):
        fig.delaxes(axes[j])

    plt.tight_layout()
    plt.show()

from sklearn.preprocessing import StandardScaler, MinMaxScaler, PowerTransformer
import numpy as np

df_transformed = df.copy()

# Standardization (Z-score normalization) for normally distributed columns
standardization_cols = ['danceability', 'energy', 'loudness']
scaler_standard = StandardScaler()
df_transformed[standardization_cols] = scaler_standard.fit_transform(df[standardization_cols])

# Min-Max Scaling for features that should retain proportion
normalization_cols = ['tempo', 'valence', 'liveness']
scaler_minmax = MinMaxScaler()
df_transformed[normalization_cols] = scaler_minmax.fit_transform(df[normalization_cols])

# Log Transformation for highly right-skewed distributions
log_transform_cols = ['track_number', 'speechiness', 'instrumentalness', 'duration_ms', 'duration_min']
for col in log_transform_cols:
    df_transformed[col] = np.log1p(df[col])  # log1p helps handle zeros

# Yeo-Johnson Transformation for mixed-distribution features
yeojohnson_cols = ['acousticness']
power_transformer_yeojohnson = PowerTransformer(method='yeo-johnson')
df_transformed[yeojohnson_cols] = power_transformer_yeojohnson.fit_transform(df[yeojohnson_cols])

# No transformation for meaningful count-based features
no_transform_cols = ['total_grammy_awards', 'total_grammy_nominations', 'year', 'time_signature', 'key']
df_transformed[no_transform_cols] = df[no_transform_cols]  # Keep them as they are

transformed_features = standardization_cols + normalization_cols + log_transform_cols + yeojohnson_cols

# Plot boxplots for original vs transformed data
plt.figure(figsize=(15, 6))
sns.boxplot(data=df[transformed_features])
plt.title("Original Data Distributions (Before Transformation)")
plt.xticks(rotation=45)
plt.show()

plt.figure(figsize=(15, 6))
sns.boxplot(data=df_transformed[transformed_features])
plt.title("Transformed Data Distributions (After Transformation)")
plt.xticks(rotation=45)
plt.show()

df_transformed.head()

# END OF ASHLEY'S PRIOR WORK

print(df_transformed.columns)

print(df_transformed["liveness"])

# Engineer date features

# Convert 'release_date' to datetime
df_transformed['release_date_parsed'] = pd.to_datetime(df_transformed['release_date_parsed'], errors='coerce')

# Extract features from 'release_date'
df_transformed['release_year'] = df_transformed['release_date_parsed'].dt.year
df_transformed['release_month'] = df_transformed['release_date_parsed'].dt.month
df_transformed['release_day'] = df_transformed['release_date_parsed'].dt.day

# Adding release day of week feature (Monday = 0 , Sunday = 6)
df_transformed['release_weekday'] = df_transformed['release_date_parsed'].dt.weekday

# Drop unnecessary columns
df_transformed = df_transformed.drop(columns=['release_date', 'year', 'release_date_parsed'])

# Transform explicit feature into binary 0/1
df_transformed['explicit'] = df_transformed['explicit'].astype(int)

# Transform mode feature into binary 0/1
df_transformed['mode'] = df_transformed['mode'].astype(int)

# Creating target variable (popularity)
df_transformed["popularity"] = df_transformed["total_grammy_awards"] + df_transformed["total_grammy_nominations"]

# Removing original columns
df_transformed.drop(columns=["total_grammy_awards", "total_grammy_nominations"], inplace=True)

# Remove highly correlated features

import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# Separate features and target
X = df_transformed.drop(columns=["popularity"])
y = df_transformed["popularity"]

# Identify non-numeric columns
non_numeric_cols = X.select_dtypes(include=['object']).columns
print("Non-numeric columns:", non_numeric_cols)

# Remove identifier columns
X = X.drop(columns=['id', 'name', 'album', 'album_id', 'artists', 'artist_ids'])

# Compute correlation matrix
corr_matrix = X.corr().abs()

# Identify highly correlated features (above 0.85 threshold)
threshold = 0.85
high_corr_features = set()

for i in range(len(corr_matrix.columns)):
    for j in range(i):
        if corr_matrix.iloc[i, j] > threshold:
            colname = corr_matrix.columns[i]
            high_corr_features.add(colname)

# Drop correlated features
X_filtered = X.drop(columns=high_corr_features)
print("Remaining features after correlation filter:", X_filtered.columns)

# Removing missing values

# Drop rows with NaNs in both X and y

X_filtered = X_filtered.dropna(subset=['release_year', 'release_month', 'release_day', 'release_weekday'])
X_filtered, y = X_filtered.align(y, join="inner", axis=0)

print(X_filtered.isnull().sum())

# Lasso Regression for Feature Selection

from sklearn.linear_model import Lasso, LassoCV
from sklearn.preprocessing import StandardScaler

# Standardize the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_filtered)

# Apply cross validation to tune alpha
lasso_cv = LassoCV(alphas=np.logspace(-4, 1, 10), cv=5)
lasso_cv.fit(X_scaled, y)

# Get the best alpha value
best_alpha = lasso_cv.alpha_
print("Optimal Alpha from LassoCV:", best_alpha)

# Fit Lasso using the optimal alpha
lasso = Lasso(alpha=best_alpha)
lasso.fit(X_scaled, y)

# Get selected features (non-zero coefficients)
selected_features = X_filtered.columns[lasso.coef_ != 0]
X_lasso_selected = X_filtered[selected_features]

print("Selected features after Lasso:", selected_features)

# Use RFE to Refine Feature Selection (choosing an optimal number of features)

from sklearn.feature_selection import RFECV
from sklearn.linear_model import LinearRegression

# Initialize RFECV with cross-validation
estimator = LinearRegression()
rfecv = RFECV(estimator, cv=5)
X_rfecv_selected = rfecv.fit_transform(X_lasso_selected, y)

# Get the best number of features
optimal_features = sum(rfecv.support_)
print("Optimal number of features:", optimal_features)

# Get the selected feature names
selected_features_rfecv = X_lasso_selected.columns[rfecv.support_]
print("Selected features after RFECV:", selected_features_rfecv)

import pandas as pd

# Convert the transformed NumPy array back to a DataFrame with the selected feature names
X_rfecv_selected_df = pd.DataFrame(X_rfecv_selected, columns=selected_features_rfecv)

# This is the final refined feature set to be used for further feature engineering
print("Final shape of X_rfecv_selected_df:", X_rfecv_selected_df.shape)

# Check how many polynomial features are needed

from sklearn.linear_model import LassoCV
from sklearn.preprocessing import PolynomialFeatures

# Generate polynomial features
poly = PolynomialFeatures(degree=2, interaction_only=False, include_bias=False)
X_poly = poly.fit_transform(X_rfecv_selected_df)

# Fit LassoCV to determine if new features are useful
lasso_cv = LassoCV(cv=5).fit(X_poly, y)

# Count selected polynomial features
num_selected = sum(lasso_cv.coef_ != 0)

print(f"Number of useful polynomial features: {num_selected}")

# Identifying useful polynomial features

import numpy as np
import pandas as pd
from sklearn.linear_model import LassoCV
from sklearn.preprocessing import PolynomialFeatures

# Generate polynomial features
poly = PolynomialFeatures(degree=2, interaction_only=False, include_bias=False)
X_poly = poly.fit_transform(X_rfecv_selected_df)

# Fit LassoCV to determine if new features are useful
lasso_cv = LassoCV(cv=5).fit(X_poly, y)

# Get the original and polynomial feature names
feature_names = poly.get_feature_names_out(X_rfecv_selected_df.columns)

# Identify selected polynomial features
selected_poly_features = np.array(feature_names)[lasso_cv.coef_ != 0]

print(f"Selected Polynomial Features ({len(selected_poly_features)}):")
print(selected_poly_features)

# Adding polynomial features in

# Create a DataFrame for polynomial features
X_poly_df = pd.DataFrame(X_poly, columns=poly.get_feature_names_out(X_rfecv_selected_df.columns), index=X_rfecv_selected_df.index)

# Keep only the selected polynomial features
X_selected_poly = X_poly_df[selected_poly_features]

# Concatenate with original features
X_final = pd.concat([X_rfecv_selected_df, X_selected_poly], axis=1)

print("Final feature set shape:", X_final.shape)

import matplotlib.pyplot as plt
from sklearn.decomposition import PCA

# Fit PCA
pca = PCA()
pca.fit(X_final)

# Plot cumulative explained variance
plt.figure(figsize=(10, 6))
plt.plot(range(1, len(pca.explained_variance_ratio_) + 1),
         np.cumsum(pca.explained_variance_ratio_), marker='o')
plt.title('Cumulative Explained Variance by Principal Components')
plt.xlabel('Number of Components')
plt.ylabel('Cumulative Explained Variance')
plt.grid()
plt.axhline(y=0.90, color='r', linestyle='--')  # Example threshold for 90%
plt.show()

from sklearn.decomposition import PCA
import pandas as pd

# Fit PCA to feature set
pca = PCA(n_components=6)
X_pca = pca.fit_transform(X_final)

# Create a DataFrame for the PCA loadings
loadings = pd.DataFrame(pca.components_, columns=X_final.columns, index=[f'PC{i+1}' for i in range(pca.n_components_)])

# Display the loadings
print("PCA Loadings:\n", loadings)

# Choose a threshold to select features for each PC
threshold = 0.1
selected_features = []

for i in range(loadings.shape[0]):
    pc_loadings = loadings.iloc[i]
    significant_features = pc_loadings[abs(pc_loadings) > threshold].index.tolist()
    selected_features.extend(significant_features)

# Remove duplicates
selected_features = list(set(selected_features))

print("Selected features based on PCA loadings:", selected_features)

# Creating final DataFrame with selected features
X_final_selected = X_final[selected_features]

# Checking DataFrame
print("Final DataFrame shape:", X_final_selected.shape)
print("Final DataFrame head:\n", X_final_selected.head())

# Saving the final DataFrame to a CSV file
X_final_selected.to_csv('final_df.csv', index=False)