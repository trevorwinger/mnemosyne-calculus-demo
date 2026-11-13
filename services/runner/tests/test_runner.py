import pytest

from runner import RunRequest, execute


def test_runs_a_small_java_program_with_standard_input():
    result = execute(RunRequest(source="""public class Main {
  public static void main(String[] args) {
    java.util.Scanner input = new java.util.Scanner(System.in);
    System.out.println(input.nextInt() + 1);
  }
}""", language="java", stdin="41"))
    assert result.status == "completed", result.stderr
    assert result.stdout.strip() == "42"


@pytest.mark.parametrize(("language", "source", "expected"), [
    ("python", "print('python')", "python"),
    ("javascript", "console.log('javascript')", "javascript"),
    ("c", "#include <stdio.h>\nint main(void) { puts(\"c\"); }", "c"),
    ("cpp", "#include <iostream>\nint main() { std::cout << \"cpp\\n\"; }", "cpp"),
])
def test_runs_each_supported_language(language, source, expected):
    result = execute(RunRequest(language=language, source=source))
    assert result.status == "completed", result.stderr
    assert result.stdout.strip() == expected


def test_returns_compile_errors_without_running_source():
    result = execute(RunRequest(language="java", source="public class Main {"))
    assert result.status == "compile_error"
    assert result.stderr


def test_stops_an_infinite_program():
    result = execute(RunRequest(source="""public class Main {
  public static void main(String[] args) {
    while (true) { }
  }
}""", language="java"))
    assert result.status == "timeout"
