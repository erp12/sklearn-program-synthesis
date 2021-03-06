import random
import math
import operator as o

from .plushi import type_to_plushi_type, run_on_dataset


class Annealer:

    def __init__(self, n_steps, initial_temp, mutation, penalty=1e3, verbose=0):
        self.n_steps = n_steps
        self.initial_temp = initial_temp
        self.current_temp = initial_temp
        self.current_step = 0
        self.mutation = mutation
        self.penalty = penalty
        self.verbose = verbose

    def _update_temp(self):
        self.current_temp = self.initial_temp - (self.current_step / self.n_steps)

    def _acceptance(self, current_error, next_error, min_or_max):
        compare_op = o.lt if min_or_max is 'min' else o.gt
        if compare_op(current_error, next_error):
            return 1
        else:
            try:
                delta_error = next_error - current_error
                return math.exp(-delta_error / self.current_temp)
            except OverflowError:
                if delta_error < 0:
                    return 1
                else:
                    return 0

    def _evaluate(self, program, X, y, metric, min_or_max):
        output_types = [type_to_plushi_type(y.dtype)]
        y_hat = run_on_dataset(program, output_types, X).flatten()

        error = 0
        valid_y_hat = []
        valid_y = []
        for i in range(len(y_hat)):
            if y_hat[i] == 'NO-STACK-ITEM':
                p = -self.penalty if min_or_max is 'max' else self.penalty
                error += p
            else:
                valid_y_hat.append(float(y_hat[i]))
                valid_y.append(float(y[i]))

        if len(valid_y) > 0:
            error += metric(valid_y, valid_y_hat)
        return error

    def search(self, X, y, metric, min_or_max='min'):
        self.current_step = 0

        current_program = self.mutation.push_spawner.random_program()
        current_error = self._evaluate(current_program, X, y, metric, min_or_max)

        while self.current_temp > 0:
            if self.verbose > 0:
                print("Temp:", round(self.current_temp, 4),
                      "Error:", round(current_error, 4),
                      "Program Size:", len(current_program))
            new_program = self.mutation.mutate(current_program)
            new_error = self._evaluate(new_program, X, y, metric, min_or_max)

            acceptance_prop = self._acceptance(current_error, new_error, min_or_max)
            if random.random() < acceptance_prop:
                current_program = new_program
                current_error = new_error

            self.current_step += 1
            self._update_temp()

        return current_program
