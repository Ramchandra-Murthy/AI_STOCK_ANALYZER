# Optional LSTM research model

This module adds a small PyTorch LSTM as an experimental comparator to the existing
scikit-learn MLP. It is not connected to production signals, paper-trading decisions,
or broker order submission.

## Dependency

PyTorch is deliberately **not** added to the core application dependencies in this
change. Install a compatible PyTorch build in a separate research environment before
calling `train_lstm_model`. The module raises an actionable error when PyTorch is
missing. This avoids silently increasing the Streamlit deployment image size or
changing the application's locked runtime dependencies.

## Validation and limitations

- Uses the existing causal feature and future-return label builder.
- Holds out the latest chronological window and purges training labels whose
  forward-return horizon overlaps the start of the holdout.
- Fits the feature scaler using training sequences only.
- Uses a fixed random seed, gradient clipping, and a small dropout layer.
- Reports accuracy and ROC-AUC; these alone do not demonstrate profitability.
- The model is a research baseline, not evidence of a tradable edge. Before any
  strategy use, compare against the existing MLP on identical walk-forward folds
  and include execution timing, transaction costs, slippage, and portfolio-level
  risk evaluation.

The holdout is used for evaluation, not gradient updates. Hyperparameter selection
must use separate chronological validation data rather than repeatedly tuning on
this holdout.
