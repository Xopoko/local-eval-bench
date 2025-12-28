# Routing

The optional router runs one md task and one py task for each candidate model.
If codegen wins on py and the main model wins on md, it routes:

- code tasks -> codegen model
- logic tasks -> main model

Otherwise, it uses a single model for all tasks.
