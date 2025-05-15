import time
import itertools as it

# Define Sudoku variables and constraints
variables = [f"{col}{row}" for row in "123456789" for col in "ABCDEFGHI"]
rows = "123456789"
cols = "ABCDEFGHI"
# Constraints represent the rows, columns, and 3x3 blocks of the Sudoku board. Each constraint is a list of cells,
# where each cell must have a unique value between 1 and 9. The constraints are defined as a list of lists.
constraints = [
    # Rows
    [f"{col}{row}" for col in cols] for row in rows
] + [
    # Columns
    [f"{col}{row}" for row in rows] for col in cols
] + [
    # 3x3 Blocks
    [f"{cols[c + dc]}{rows[r + dr]}" for dr in range(3) for dc in range(3)]
    for r in range(0, 9, 3)
    for c in range(0, 9, 3)
]


def load_board(verbose=False):
    """
    Reads an input file to initialize the Sudoku board.
    The cells are loaded from the "board" file with values between 1 and 9.

    Args:
        verbose (bool): If True, shows information about each initialized cell.

    Returns:
        dict: A dictionary of possible values for each cell. If the value of a cell is defined
                in the input file, the set contains only that value, otherwise it contains all values from
                1 to 9.
    """
    varsValues = {f"{col}{row}": set(range(1, 10))
                  for row, col in it.product("123456789", "ABCDEFGHI")}
    filePath = "a"
    with open(filePath) as board_fd:
        for key in varsValues:
            keyValue = int(board_fd.readline().strip())
            if keyValue < 10:
                varsValues[key] = {keyValue}
                if verbose:
                    print(f"Initializing: {key} = {keyValue}")
    return varsValues


def apply_constraints(varsValues, verbose=False):
    """
    Iterate through the constrained cells, looking for cells with a single value and removing that value from its peers.

    Args:
        varsValues (dict): Dictionary of possible values for each cell.
        verbose (bool): If True, shows the values removed from each cell.

    Returns:
        dict: Updated dictionary of possible values for each cell.
    """
    dirty = True
    while dirty:
        dirty = False
        for constraint in constraints:
            for cellId in constraint:
                # This cell has been solved, remove the value from its peers possible values.
                if len(varsValues[cellId]) == 1:
                    # Get the single value
                    unique_value = next(iter(varsValues[cellId]))
                    for key in constraint:
                        if key != cellId and unique_value in varsValues[key]:
                            varsValues[key].discard(unique_value)
                            dirty = True  # Prompt another iteration due to the change in the possible values
                            if verbose:
                                print(f"Removing {unique_value} from {
                                      key} due to {cellId} = {unique_value}")
    return varsValues


def move(y, x):
    import sys
    sys.stdout.write("\033[%d;%dH" % (y, x))


def look_forward(varsValues, verbose=False, step_by_step=False):
    """
    Look-forward algorithm to solve the Sudoku by assigning values and propagating constraints.
    The algorithm takes a recursive approach to solve the board, backtracking if a dead-end is reached.
    At the beginning, a cell is chosen heuristically, and from it, the algorithm tries to find a solution by testing
    each possible value for that cell. If a value is found to be valid for the current state of the board, the algorithm
    proceeds to the next cell, and so on. If a cell is left without possible values, the algorithm backtracks to the
    last decision where the path was viable and tries the next possible value.

    Args:
        VarsValues (dict): Dictionary of possible values for each cell.
        verbose (bool): If True, shows the details of each assignment and propagation.
        step_by_step (bool): If True, shows the board at each step and dramatically pause between steps.

    Returns:
        dict or None: Dictionary with the complete solution if found, or None if no solution is found.
    """
    if step_by_step:
        move(0, 0)
        stylized_board(varsValues)
        time.sleep(0.5)
    unassigned_vars = [var for var in varsValues if len(varsValues[var]) > 1]
    if not unassigned_vars:
        return varsValues  # Solution found

    # Heuristic: select the cell with the fewest potential values
    chosen = min(unassigned_vars, key=lambda v: len(varsValues[v]))

    if verbose:
        print(f"\nSelecting {chosen} with possible values: {
              varsValues[chosen]}. {len(unassigned_vars)} unassigned cells remaining.")

    # Evaluate the viability of assigning each possible value to the chosen cell
    for value in varsValues[chosen].copy():
        if verbose:
            print(f"Trying to assign {chosen} = {value}")

        # Deep copy the board dictionary to avoid modifying the original
        new_varsValues = {k: v.copy() for k, v in varsValues.items()}
        # Assign the value to the chosen cell
        new_varsValues[chosen] = {value}

        # Constraint propagation: remove the value from neighbors
        if propagate_constraints(new_varsValues, chosen, value, verbose, step_by_step):
            # This value it's valid for the immediate step
            result = look_forward(new_varsValues, verbose, step_by_step)
            if result:
                # The path leads to a valid solution
                return result  # Complete solution found
            # If the path leads to a dead-end, try the next value

    # There is not possible solution to the current board.
    return None


def propagate_constraints(varsValues, var, value, verbose=False, step_by_step=False):
    """
    Propagates constraints by removing a value from the pool of possible values of the neighbors of a cell.

    Args:
        varsValues (dict): Dictionary of possible values for each cell.
        var (str): The cell to which the value was assigned.
        value (int): The value assigned to the cell `var`.
        verbose (bool): If True, shows the details of each propagation.
        step_by_step (bool): If True, shows the board at each step and dramatically pause between steps.

    Returns:
        bool: True if the propagation is successful, False if any cell is left without values.
    """
    for constraint in constraints:
        if var in constraint:
            for peer in constraint:
                if peer != var and value in varsValues[peer]:
                    # Remove the value from the possible values of the peer cell.
                    varsValues[peer].discard(value)
                    if verbose:
                        print(f"Propagating: removing {value} from {peer}.")

                    if step_by_step and len(varsValues[peer]) <= 1:
                        move(0, 0)
                        stylized_board(varsValues)
                        if len(varsValues[peer]) == 0:
                            time.sleep(1)
                        else:
                            time.sleep(0.1)

                    # If a cell is left without possible values, stop propagation.
                    if len(varsValues[peer]) == 0:
                        if verbose:
                            print(f"Error: assigning {value} to {var} leaves {
                                  peer} without possible values.")
                        return False
                    # If a cell has a single value, propagate that value additionally.
                    elif len(varsValues[peer]) == 1:
                        next_value = next(iter(varsValues[peer]))
                        if verbose:
                            print(f"{peer} reduced to a single value {
                                  next_value}.")
                        if not propagate_constraints(varsValues, peer, next_value, verbose, step_by_step):
                            return False
    return True


def stylized_board(varsValues):
    """
    Prints the Sudoku board in a stylized format.

    Args:
        varsValues (dict): Dictionary of possible values for each cell.
    """
    horizontal_border = "╔═══════╦═══════╦═══════╗"
    middle_border = "╠═══════╬═══════╬═══════╣"
    bottom_border = "╚═══════╩═══════╩═══════╝"
    row_separator = "║"

    print(horizontal_border)
    for i, row in enumerate(rows):
        row_values = []
        for col in cols:
            cell_values = list(varsValues[f"{col}{row}"])
            if len(cell_values) == 1:
                row_values.append(str(cell_values[0]))
            elif len(cell_values) == 0:
                row_values.append('!')
            else:
                row_values.append('.')
        row_values = " ".join(row_values)
        print(f"{row_separator} {row_values[:5]} {row_separator} {
              row_values[6:11]} {row_separator} {row_values[12:]} {row_separator}")
        if i == 2 or i == 5:
            print(middle_border)
    print(bottom_border)

# Main program

# do not activate both verbose and step_by_step at the same time
verbose = False #activate to see the details of each step
step_by_step = True #activate to see the board at each step

if step_by_step:
    import os
    os.system('cls' if os.name == 'nt' else 'clear')
# Load the board from the input file
varsValues = load_board(verbose)
# Trim possible values based on the predefined cells in the board
varsValues = apply_constraints(varsValues, verbose)
# Solve the Sudoku
solution = look_forward(varsValues, verbose, step_by_step)

# Show solution
if solution:
    if not step_by_step:
        print("\nSolution found:")
        stylized_board(solution)
else:
    if step_by_step:
        move(0, 0)
    print("No solution found.")
