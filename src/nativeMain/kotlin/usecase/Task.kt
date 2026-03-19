package usecase

// Definition for a task:
// * simple task to carry out in the system.

// Assumptions for task execution:
// * it does not report back to any presentation layer.
// * it might have side effects must most commonly only returns a result
// * assumes that interactors (who are using tasks) have loaded required services
interface Task {}