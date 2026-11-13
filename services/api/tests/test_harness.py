import asyncio

from app.harness import SYSTEM_POLICY, classify_action, conversation_relevance, course_relevance, scope_response, validate
import app.main as main
from app.providers import AvailableModel

def test_final_answer_request_is_redirected():
    response = validate("A plausible answer", "Please give me the final answer to my assignment")
    assert response.action == "redirect_to_attempt"
    assert "submission-ready" in response.content

def test_unchecked_complete_solution_is_replaced():
    response = validate("Here is the complete solution\n```java\n" + "x" * 1000, "How should I start?")
    assert response.changed
    assert "manageable step" in response.content


def test_system_policy_requires_course_scoped_tutoring():
    assert "only the current course" in SYSTEM_POLICY
    assert "Do not answer unrelated questions" in SYSTEM_POLICY
    assert "before helping" in SYSTEM_POLICY


def test_calculus_is_refused_in_an_algebra_course_before_model_generation():
    algebra_context = "MATH-113 Algebra with Applications. Solve equations and inequalities. Quadratics, exponents, logarithms, and functions."
    relevance = course_relevance("Can you explain derivatives and integrals?", algebra_context)
    response = scope_response("MATH-113: Algebra with Applications", relevance)
    assert relevance == "out_of_scope"
    assert response.action == "out_of_scope"
    assert "can’t help" in response.content


def test_known_course_topics_are_allowed_and_unknown_topics_are_clarified():
    algebra_context = "MATH-113 Algebra with Applications. Solve equations and inequalities. Quadratics, exponents, logarithms, and functions."
    assert course_relevance("How do I factor a quadratic?", algebra_context) == "related"
    assert course_relevance("What is the best dinner recipe?", algebra_context) == "out_of_scope"
    assert course_relevance("Can you help me with this?", algebra_context) == "needs_clarification"


def test_ambiguous_follow_up_keeps_the_recent_course_context():
    calculus_context = "MATH-240 Calculus and Analytic Geometry I. Limits, derivatives, chain rule, and rates of change."
    previous = ["How do I take the derivative of x times e to the negative x?"]
    assert conversation_relevance("Help me figure out the next steps.", calculus_context, previous) == "related"
    assert conversation_relevance("This was covered in class, but the course material may not be available yet.", calculus_context, [*previous, "Help me figure out the next steps."]) == "related"

    programming_context = "CSCI-201 Introduction to Programming in Java. Variables, loops, methods, arrays, and recursion."
    programming_previous = ["How should I trace the last array loop iteration?"]
    assert conversation_relevance("Can you help me with the next step?", programming_context, programming_previous) == "related"


def test_short_numeric_reply_stays_in_a_tutor_led_course_problem():
    calculus_context = "MATH-240 Calculus and Analytic Geometry I. Limits, derivatives, and the chain rule."
    assert conversation_relevance("15", calculus_context, ["How do I take a derivative?", "3", "8"], ["What is the next value?"]) == "related"


def test_short_reply_without_an_established_course_thread_does_not_inherit_context():
    calculus_context = "MATH 242 Calculus and Analytic Geometry III. Vectors and dot products."
    assert conversation_relevance("15", calculus_context, ["Hello", "okay"], ["Good work."]) == "needs_clarification"


def test_explicitly_off_topic_follow_up_does_not_inherit_course_context():
    calculus_context = "MATH-240 Calculus and Analytic Geometry I. Limits, derivatives, chain rule, and rates of change."
    assert conversation_relevance("What is a good dinner recipe?", calculus_context, ["How do I take the derivative?"]) == "out_of_scope"


def test_rejected_candidate_is_regenerated_once(monkeypatch):
    calls = 0

    async def generated(*_args):
        nonlocal calls
        calls += 1
        return ("Here is the complete solution" if calls == 1 else "Start by writing down the loop's last valid index.", 3, None, None)

    monkeypatch.setattr(main, "generate_until_disconnected", generated)
    model = AvailableModel("demo-tutor", None, None, None, None, "demo", True)
    checked, _, _, _, attempts = asyncio.run(main.generate_checked_response(object(), model, [], "How do I start this loop?"))
    assert checked.content.startswith("Start by")
    assert attempts == calls == 2
