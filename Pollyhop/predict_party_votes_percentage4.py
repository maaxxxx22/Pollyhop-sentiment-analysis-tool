import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImbPipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from sklearn.metrics import classification_report

# Load the data
df = pd.read_csv('data/1976-2020-president.csv')

# Simplify party labels
def simplify_party(party):
    if party in ["DEMOCRAT", "REPUBLICAN", "INDEPENDENT"]:
        return party
    else:
        return "OTHER"

df['party_simplified'] = df['party_detailed'].apply(simplify_party)

# Separate features and target
X = df.drop(columns=['party_simplified', 'notes', 'party_detailed'])
y = df['party_simplified']

# Identify categorical and numerical columns
categorical_cols = X.select_dtypes(include=['object']).columns
numerical_cols = X.select_dtypes(exclude=['object']).columns

# Convert all values in categorical columns to strings
X[categorical_cols] = X[categorical_cols].astype(str)

# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

# Check for data leakage
assert set(X_train.index).isdisjoint(X_test.index), "Data leakage: Train and Test sets overlap"

# Preprocessing for numerical data: impute missing values and scale
numerical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='mean')),
    ('scaler', StandardScaler())
])

# Preprocessing for categorical data: impute missing values and one-hot encode
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))
])

# Bundle preprocessing for numerical and categorical data
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_cols),
        ('cat', categorical_transformer, categorical_cols)
    ])

# Define the model
model = ImbPipeline(steps=[
    ('preprocessor', preprocessor),
    ('smote', SMOTE(random_state=42)),
    ('classifier', LogisticRegression(max_iter=1000))
])

# Train the model
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
accuracy = (y_pred == y_test).mean()
print(f'Accuracy: {accuracy}')

# Classification report
print(classification_report(y_test, y_pred))

# Predict probabilities
probabilities = model.predict_proba(X_test)

# Convert to DataFrame
prob_df = pd.DataFrame(probabilities, columns=model.classes_)
prob_df['state'] = X_test['state'].values

print(f'Shape of probabilities DataFrame: {prob_df.shape}')
print(prob_df.head())

# Check class balance
class_counts = pd.Series(y_train).value_counts()

# Number of unique parties
num_other_parties = 153  # Based on the previously found count
num_independent_parties = 17  # Based on the previously found count

# Adjust the 'OTHER' and 'INDEPENDENT' categories by dividing their counts by the number of unique parties
class_counts['OTHER'] = class_counts['OTHER'] / num_other_parties
class_counts['INDEPENDENT'] = class_counts['INDEPENDENT'] / num_independent_parties

print("Class distribution after resampling:")
print(class_counts)

# Create historical_data DataFrame
historical_data = prob_df[['state'] + model.classes_.tolist()]
historical_data = historical_data.melt(id_vars=['state'], var_name='candidate_name', value_name='historical_pct')
print(historical_data)

# Ensure the historical_data DataFrame is available in the globals
globals()['historical_data'] = historical_data
