import os
from sympy.integrals.rubi.symbol import WC
import matchpy
from cpp_code_generation import CppCodeGenerator
from symengine_printer import symengine_print
from sympy import *

x, y, z = symbols("x y z")
a, b, c = symbols("a b c")
f = Function("f")
w = WC("w")


collection_of_expressions = [
        ([x], {x: True, y: False}),
        ([x**y], {x**y: True, x**z: False}),
        ([x**y, w], {x**y: True, x: True, x+y: True}),
        #([x+y], {}),
]

def generate_matchpy_matcher(pattern_list):
    matcher = matchpy.ManyToOneMatcher()
    for pattern in pattern_list:
        matcher.add(matchpy.Pattern(pattern))
    return matcher


def generate_cpp_code(matcher):
    cg = CppCodeGenerator(matcher)
    a, b = cg.generate_code()
    return a, b


def export_code_to_file(filename, a, b):
    fout = open(os.path.join("tests", filename), "w")
    fout.write(a)
    fout.write("\n\n")
    fout.write(b)
    return fout


def add_main_with_tests(fout, test_cases):
    fout.write("""
int main() {
    tuple<int, Substitution> ret;

""")
    for test_case, result in test_cases.items():
        fout.write("    ret = match_root({0});\n".format(symengine_print(test_case)))
        if result:
            fout.write("    assert(get<0>(ret) >= 0);\n")
        else:
            fout.write("    assert(get<0>(ret) == -1);\n")
    fout.write("}\n")


def generate_tests():
    fout = open(os.path.join("tests", "CMakeLists.txt"), "w")
    fout.write("""\
project(matchpycpp_tests)

include_directories(BEFORE ${symengine_SOURCE_DIR})
include_directories(BEFORE ${symengine_BINARY_DIR})
include_directories(BEFORE ${teuchos_SOURCE_DIR})
include_directories(BEFORE ${teuchos_BINARY_DIR})
""")
    for i, (pattern_list, test_cases) in enumerate(collection_of_expressions):
        matcher = generate_matchpy_matcher(pattern_list)
        a, b = generate_cpp_code(matcher)
        filename = "test_case{0:03}".format(i)
        filenamecpp = "{}.cpp".format(filename)
        fwrite = export_code_to_file(filenamecpp, a, b)
        add_main_with_tests(fwrite, test_cases)
        fwrite.close()
        fout.write("\n")
        fout.write("add_executable({0} {1})\n".format(filename, filenamecpp))
        fout.write("target_link_libraries({0} symengine)\n".format(filename))
    fout.close()


if __name__ == "__main__":
    generate_tests()
