import math


# ============================================================
# CONSTANTS
# ============================================================

PI = math.pi


# ============================================================
# IDENTITY MATRIX
#
# Returns a 3x3 identity matrix as a list of lists.
# Equivalent to C++: void identity(float A[3][3])
# ============================================================

def identity():
    """
    Build and return a 3x3 identity matrix.

    [ 1  0  0 ]
    [ 0  1  0 ]
    [ 0  0  1 ]
    """

    return [
        [1.0, 0.0, 0.0],
        [0.0, 1.0, 0.0],
        [0.0, 0.0, 1.0],
    ]


# ============================================================
# PRINT MATRIX
#
# Prints a 3x3 matrix to stdout.
# Equivalent to C++: void printMatrix(float A[3][3])
# ============================================================

def print_matrix(A):
    """
    Print a 3x3 homogeneous matrix to the console.
    """

    print()

    for i in range(3):

        row_str = ""

        for j in range(3):
            row_str += f"{A[i][j]:.4f}\t"

        print(row_str)


# ============================================================
# MATRIX MULTIPLICATION
#
# C = A x B  (3x3)
# Equivalent to C++: void multiplyMatrix(A, B, C)
# ============================================================

def multiply_matrix(A, B):
    """
    Multiply two 3x3 matrices A and B.
    Returns the resulting 3x3 matrix C = A x B.
    """

    C = [
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
        [0.0, 0.0, 0.0],
    ]

    for i in range(3):
        for j in range(3):
            for k in range(3):
                C[i][j] += A[i][k] * B[k][j]

    return C


# ============================================================
# PRINT POINTS
#
# Prints point coordinates in homogeneous form.
# Equivalent to C++: void printPoints(float x[], float y[], int n)
# ============================================================

def print_points(points):
    """
    Print coordinate matrix in homogeneous form.

    points: list of (x, y) tuples
    """

    print("\nCoordinate Matrix\n")
    print("X\t\tY\t\t1")

    for (x, y) in points:
        print(f"{x:.4f}\t\t{y:.4f}\t\t1")


# ============================================================
# TRANSLATION MATRIX
#
# Supports both Row and Column homogeneous representations.
# Equivalent to C++: void translationMatrix(T, tx, ty, type)
#
# type == 1 : Row Matrix
#   [ 1   0   0 ]
#   [ 0   1   0 ]
#   [ tx  ty  1 ]
#
# type == 2 : Column Matrix
#   [ 1   0   tx ]
#   [ 0   1   ty ]
#   [ 0   0   1  ]
# ============================================================

def translation_matrix(tx, ty, rep_type):
    """
    Build a 3x3 translation matrix.

    rep_type : 1 = Row representation
               2 = Column representation
    """

    T = identity()

    if rep_type == 1:

        # Row Matrix
        T[2][0] = tx
        T[2][1] = ty

    else:

        # Column Matrix
        T[0][2] = tx
        T[1][2] = ty

    return T


# ============================================================
# SCALING MATRIX
#
# Equivalent to C++: void scalingMatrix(T, sx, sy)
#
# [ sx  0   0 ]
# [ 0   sy  0 ]
# [ 0   0   1 ]
# ============================================================

def scaling_matrix(sx, sy):
    """
    Build a 3x3 uniform/non-uniform scaling matrix.
    Scaling is representation-independent (same for row/column).
    """

    T = identity()

    T[0][0] = sx
    T[1][1] = sy

    return T


# ============================================================
# ROTATION MATRIX
#
# Equivalent to C++: void rotationMatrix(T, angle, type)
#
# type == 1 : Row Matrix (point is row vector [x y 1])
#   [ cos   -sin   0 ]
#   [ sin    cos   0 ]
#   [ 0      0     1 ]
#
# type == 2 : Column Matrix (point is column vector)
#   [ cos    sin   0 ]
#   [ -sin   cos   0 ]
#   [ 0      0     1 ]
# ============================================================

def rotation_matrix(angle_deg, rep_type):
    """
    Build a 3x3 rotation matrix.

    angle_deg : angle in degrees
                positive = anticlockwise
                negative = clockwise
    rep_type  : 1 = Row representation
                2 = Column representation
    """

    T = identity()

    rad = angle_deg * PI / 180.0

    c = math.cos(rad)
    s = math.sin(rad)

    if rep_type == 1:

        # Row Matrix
        T[0][0] =  c
        T[0][1] = -s

        T[1][0] =  s
        T[1][1] =  c

    else:

        # Column Matrix
        T[0][0] =  c
        T[0][1] =  s

        T[1][0] = -s
        T[1][1] =  c

    return T


# ============================================================
# APPLY TRANSFORMATION
#
# Applies a 3x3 matrix T to each point in points list.
# Equivalent to C++: void applyTransformation(T, ox, oy, nx, ny, n, type)
#
# Returns a new list of (x, y) transformed points.
# ============================================================

def apply_transformation(T, points, rep_type):
    """
    Apply transformation matrix T to a list of (x, y) points.

    T         : 3x3 homogeneous matrix
    points    : list of (x, y) tuples
    rep_type  : 1 = Row  (P * T)
                2 = Column (T * P)

    Returns list of transformed (x, y) tuples.
    """

    transformed = []

    for (ox, oy) in points:

        # Homogeneous point vector P = [x, y, 1]
        P = [ox, oy, 1.0]

        result = [0.0, 0.0, 0.0]

        if rep_type == 1:

            # ------------------------------------------------
            # ROW MATRIX: result = P * T
            # result[j] = sum over k of P[k] * T[k][j]
            # ------------------------------------------------

            for j in range(3):
                for k in range(3):
                    result[j] += P[k] * T[k][j]

        else:

            # ------------------------------------------------
            # COLUMN MATRIX: result = T * P
            # result[j] = sum over k of T[j][k] * P[k]
            # ------------------------------------------------

            for j in range(3):
                for k in range(3):
                    result[j] += T[j][k] * P[k]

        transformed.append((result[0], result[1]))

    return transformed


# ============================================================
# BUILD COMPOSITE TRANSFORMATION
#
# Chains multiple transformations (T, S, R) in sequence.
# Equivalent to C++: void buildComposite(Final, type)
#
# Returns the final composite 3x3 matrix.
# ============================================================

def build_composite(rep_type):
    """
    Interactively build a composite transformation matrix
    by chaining T (Translation), S (Scaling), R (Rotation).

    rep_type : 1 = Row, 2 = Column

    Returns the final 3x3 composite matrix.
    """

    Final = identity()

    print("\nEnter sequence")
    print("T = Translation")
    print("S = Scaling")
    print("R = Rotation")
    print("Example: TSR")

    seq = input("\nSequence : ").strip()

    for ch in seq:

        T = identity()

        # --------------------------------------------------------
        # TRANSLATION
        # --------------------------------------------------------

        if ch in ('T', 't'):

            tx = float(input("\nEnter tx : "))
            ty = float(input("Enter ty : "))

            T = translation_matrix(tx, ty, rep_type)

            print("\nTranslation Matrix")
            print_matrix(T)


        # --------------------------------------------------------
        # SCALING
        # --------------------------------------------------------

        elif ch in ('S', 's'):

            sx = float(input("\nEnter sx : "))
            sy = float(input("Enter sy : "))

            T = scaling_matrix(sx, sy)

            print("\nScaling Matrix")
            print_matrix(T)


        # --------------------------------------------------------
        # ROTATION
        # --------------------------------------------------------

        elif ch in ('R', 'r'):

            print("\n1. Clockwise")
            print("2. Anticlockwise")

            direction = int(input("\nEnter Rotation Direction : "))

            if direction not in (1, 2):
                print("\nInvalid Rotation Direction")
                continue

            angle = float(input("Enter Angle : "))

            if direction == 1:
                # Clockwise → negate angle
                angle = -angle

            T = rotation_matrix(angle, rep_type)

            print("\nRotation Matrix")
            print_matrix(T)


        # --------------------------------------------------------
        # INVALID
        # --------------------------------------------------------

        else:
            print(f"\nInvalid Operation: {ch}")
            continue


        # --------------------------------------------------------
        # COMPOSITE ACCUMULATION
        #
        # Row    : Final = Final * T
        # Column : Final = T * Final
        # --------------------------------------------------------

        if rep_type == 1:
            Final = multiply_matrix(Final, T)
        else:
            Final = multiply_matrix(T, Final)

    return Final
