"""Offline Unit 4 regression tests; no provider, API, or credentials needed."""
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1] / "projects/gaia-final-agent"


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


agent = load("gaia_capstone_agent", "agent.py")
benchmark = load("gaia_capstone_benchmark", "benchmark.py")
sys.modules["agent"] = agent
sys.modules["benchmark"] = benchmark
cli = load("gaia_capstone_cli", "cli.py")


class GaiaAgentTests(unittest.TestCase):
    def test_calculator_order_of_operations(self):
        self.assertEqual(agent.calculate("2 + 3 * 4"), "14")

    def test_mlb_batting_extreme_uses_team_and_player_stats(self):
        teams = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"teams": [
                {"id": 1, "name": "Boston Red Sox"},
                {"id": 2, "name": "New York Yankees"},
            ]},
        )
        stats = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"stats": [{"splits": [
                {"stat": {"baseOnBalls": 40, "atBats": 500}},
                {"stat": {"baseOnBalls": 72, "atBats": 481}},
            ]}]},
        )
        question = "How many at bats did the Yankee with the most walks in the 1977 regular season have?"
        with patch("requests.get", side_effect=[teams, stats]) as get:
            self.assertEqual(agent.mlb_team_batting_extreme(question), "481")
        self.assertEqual(get.call_args_list[1].kwargs["params"]["teamId"], 2)

    def test_npb_roster_uses_year_and_adjacent_uniform_numbers(self):
        player = "|team=Hokkaido Nippon Ham Fighters\n|number=19"
        question = (
            "Who are the pitchers with the number before and after Taishō Tamai's number "
            "as of July 2023?"
        )
        roster = "吉田\nヨシダ\n輝星\n18 投手\n玉井\nタマイ\n大翔\n19 投手\n上原\nウエハラ\n健太\n20 投手"
        response = SimpleNamespace(content=b"pdf", raise_for_status=lambda: None)
        with patch.object(agent, "wikipedia", return_value=player), patch.object(
                agent, "_validate_public_url"), patch.object(
                agent, "_pdf_text", return_value=roster), patch(
                "requests.get", return_value=response) as get:
            answer = agent.npb_adjacent_pitchers(question)
        self.assertEqual(answer, "Yoshida, Uehara")
        self.assertIn("f2023.pdf", get.call_args.args[0])
        self.assertEqual(agent.calculate("-(10 - 3)"), "-7")

    def test_calculator_rejects_code_and_resource_exhaustion(self):
        for expression in ['__import__("os")', '2 ** 10000000', '[1] * 100000', '"a" * 10']:
            with self.subTest(expression=expression), self.assertRaises((ValueError, SyntaxError)):
                agent.calculate(expression)

    def test_table_aggregation_is_bounded_and_deterministic(self):
        self.assertEqual(agent.aggregate_numbers([1.25, 2.75, 6], "sum"), "10.0")
        self.assertEqual(agent.aggregate_numbers([4, 8], "count"), "2")
        with self.assertRaises(ValueError):
            agent.aggregate_numbers([1, float("nan")], "sum")

    def test_operation_table_counterexamples_are_computed(self):
        table = """|*|a|b|c|
|---|---|---|---|
|a|a|a|c|
|b|b|b|c|
|c|c|c|c|"""
        self.assertEqual(agent.commutativity_counterexample_elements(table), ["a", "b"])

    def test_attachment_text_and_missing_file(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "evidence.txt"
            path.write_text("Relevant evidence", encoding="utf-8")
            self.assertEqual(agent.read_attachment(str(path)), "Relevant evidence")
            with self.assertRaises(FileNotFoundError):
                agent.read_attachment(str(path.with_name("missing.txt")))

    def test_python_attachment_is_read_but_never_executed(self):
        with tempfile.TemporaryDirectory() as temporary:
            marker = Path(temporary) / "executed.txt"
            code = Path(temporary) / "question.py"
            code.write_text(f"open({str(marker)!r}, 'w').write('bad')", encoding="utf-8")
            self.assertIn("open(", agent.read_attachment(str(code)))
            self.assertIn("STATIC AST FACTS", agent.read_attachment(str(code)))
            self.assertFalse(marker.exists())

    def test_image_attachment_uses_local_vision(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "photo.png"
            path.write_bytes(b"not a photo")
            with patch.object(agent, "analyze_image", return_value="visible evidence") as vision:
                self.assertEqual(
                    agent.read_attachment(str(path), "What is visible?"), "visible evidence"
                )
            vision.assert_called_once_with(str(path), "What is visible?")

    def test_vision_runtime_failure_is_reported_as_unsupported(self):
        response = SimpleNamespace(
            ok=False, status_code=500, text="", json=lambda: {"error": "runner crashed"}
        )
        with tempfile.TemporaryDirectory() as temporary:
            image = Path(temporary) / "image.png"
            image.write_bytes(b"image")
            with patch("requests.post", return_value=response), self.assertRaisesRegex(
                    agent.UnsupportedCapabilityError, "runner crashed"):
                agent._ollama_vision(str(image), "Describe it")

    def test_linked_video_uses_local_media_analysis(self):
        create = Mock(return_value=SimpleNamespace(choices=[SimpleNamespace(
            message=SimpleNamespace(content="4", tool_calls=[]))]))
        bot = agent.GAIAAgent(client=SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create))), environment={})
        question = "In the video https://youtube.com/watch?v=abcdefghi, what is visible?"
        with patch.object(agent, "analyze_video_url", return_value="four birds") as video:
            self.assertEqual(bot.answer(question), "4")
        video.assert_called_once_with("https://youtube.com/watch?v=abcdefghi", question)

    def test_speech_video_downloads_audio_only(self):
        captured = {}

        class FakeYoutubeDL:
            def __init__(self, options):
                captured.update(options)

            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def download(self, _):
                Path(captured["outtmpl"].replace("%(ext)s", "m4a")).write_bytes(b"audio")

        fake_module = SimpleNamespace(YoutubeDL=FakeYoutubeDL)
        question = "What does the actor say in response to the question?"
        with patch.dict(sys.modules, {"yt_dlp": fake_module}), patch.object(
                agent, "transcribe_media", return_value="transcript"):
            self.assertEqual(agent.analyze_video_url(
                "https://youtube.com/watch?v=abcdefghi", question), "transcript")
        self.assertEqual(captured["format"], "bestaudio/best")

    def test_audio_attachment_uses_local_transcription(self):
        segment = SimpleNamespace(text=" pages 12 through 14 ")
        model = SimpleNamespace(transcribe=Mock(return_value=([segment], object())))
        with patch.object(agent, "_whisper_model", return_value=model):
            self.assertIn("pages 12 through 14", agent.transcribe_media("audio.mp3"))
        model.transcribe.assert_called_once()

    def test_repetitive_generation_is_repaired_once(self):
        create = Mock(side_effect=[
            SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content="milk " * 100, tool_calls=[]))]),
            SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
                content="broccoli", tool_calls=[]))]),
        ])
        bot = agent.GAIAAgent(client=SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create))), environment={
                "GAIA_MAX_TOKENS": "128", "GAIA_REPEAT_PENALTY": "1.2"})
        self.assertEqual(bot.answer("Name the vegetable."), "broccoli")
        self.assertEqual(create.call_count, 2)
        self.assertEqual(create.call_args.kwargs["max_tokens"], 128)
        self.assertFalse(create.call_args.kwargs["extra_body"]["think"])
        self.assertEqual(create.call_args.kwargs["extra_body"]["options"]["repeat_penalty"], 1.2)

    def test_local_model_override_does_not_change_other_projects(self):
        bot = agent.GAIAAgent(client=object(), environment={}, model="qwen2:7b")
        self.assertEqual(bot.model, "qwen2:7b")
        self.assertEqual(bot.max_tokens, 300)

    def test_qwen35_reserves_budget_for_reasoning_and_answer(self):
        bot = agent.GAIAAgent(client=object(), environment={}, model="qwen3.5:9b")
        self.assertEqual(bot.max_tokens, 768)

    def test_read_web_page_extracts_source_text(self):
        response = SimpleNamespace(
            is_redirect=False, is_permanent_redirect=False,
            headers={"Content-Type": "text/html"},
            text="<html><script>ignore()</script><body>Verified fact</body></html>",
            raise_for_status=lambda: None)
        with patch.object(agent, "_validate_public_url"), patch(
                "requests.get", return_value=response) as get:
            result = agent.read_web_page("https://example.com/source")
        self.assertIn("SOURCE: https://example.com/source", result)
        self.assertIn("Verified fact", result)
        self.assertNotIn("ignore", result)
        self.assertFalse(get.call_args.kwargs["allow_redirects"])

    def test_libretexts_transclusion_returns_relevant_source(self):
        page = SimpleNamespace(
            is_redirect=False, is_permanent_redirect=False,
            headers={"Content-Type": "text/html"},
            text='<div data-page="Books/1.E:_Exercises"></div>',
            raise_for_status=lambda: None,
        )
        source = SimpleNamespace(
            text="&lt;p&gt;A horse doctor named Louvrier treated cattle.&lt;/p&gt;",
            raise_for_status=lambda: None,
        )
        with patch.object(agent, "_validate_public_url"), patch(
                "requests.get", side_effect=[page, source]):
            result = agent.read_web_page(
                "https://chem.libretexts.org/Courses/Book/Exercises",
                "surname of the equine veterinarian",
            )
        self.assertIn("horse doctor named Louvrier", result)

    def test_read_web_page_extracts_bounded_pdf(self):
        response = SimpleNamespace(
            is_redirect=False, is_permanent_redirect=False,
            headers={"Content-Type": "application/pdf"}, content=b"pdf",
            raise_for_status=lambda: None,
        )
        page = SimpleNamespace(extract_text=lambda: "18 Yoshida\n20 Uehara")
        with patch.object(agent, "_validate_public_url"), patch(
                "requests.get", return_value=response), patch(
                "pypdf.PdfReader", return_value=SimpleNamespace(pages=[page])):
            result = agent.read_web_page("https://example.com/roster.pdf", "roster 18 20")
        self.assertIn("18 Yoshida", result)

    def test_wikipedia_returns_bounded_article_evidence(self):
        search = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"search": [{"title": "Example"}]}})
        article = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"pages": [{"title": "Example",
                                                "extract": "Verified article text"}]}})
        with patch("requests.get", side_effect=[search, article]) as get:
            evidence = agent.wikipedia("example")
        self.assertIn("ARTICLE: Example", evidence)
        self.assertIn("Verified article text", evidence)
        self.assertEqual(get.call_count, 2)

    def test_wikipedia_featured_article_question_routes_to_monthly_log(self):
        search = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"search": [{"title":
                "Wikipedia:Featured article candidates/Featured log/November 2016"}]}})
        article = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"pages": [{"extract": "Nominator details"}]}})
        rendered = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"parse": {"text": "<p>Dinosaur nominator details</p>"}})
        with patch("requests.get", side_effect=[search, article, rendered]) as get:
            agent.wikipedia(
                "Who nominated the Featured Article promoted in November 2016 on English Wikipedia?")
        self.assertEqual(
            get.call_args_list[0].kwargs["params"]["srsearch"],
            "Wikipedia:Featured article candidates/Featured log/November 2016")
        self.assertEqual(get.call_args.kwargs["timeout"], 30)
        self.assertIn("GAIAUnit4LocalAgent", get.call_args.kwargs["headers"]["User-Agent"])

    def test_wikipedia_routes_dated_event_to_specific_article(self):
        search = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"search": [{"title": "1928 Summer Olympics"}]}})
        article = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"pages": [{"extract": "Participating nations"}]}})
        with patch("requests.get", side_effect=[search, article]) as get:
            agent.wikipedia("What country sent the fewest athletes to the 1928 Summer Olympics?")
        self.assertEqual(get.call_args_list[0].kwargs["params"]["srsearch"],
                         "1928 Summer Olympics")

    def test_wikipedia_routes_regular_season_to_team_season(self):
        search = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"search": [{"title": "1977 New York Yankees season"}]}})
        article = SimpleNamespace(
            raise_for_status=lambda: None,
            json=lambda: {"query": {"pages": [{"extract": "Batting statistics"}]}})
        with patch("requests.get", side_effect=[search, article]) as get:
            agent.wikipedia("How many at bats did the Yankee with the most walks in the 1977 regular season have?")
        self.assertEqual(get.call_args_list[0].kwargs["params"]["srsearch"],
                         "1977 Yankee season")

    def test_hf_requires_separate_live_opt_in(self):
        with self.assertRaisesRegex(RuntimeError, "HF_TOKEN"):
            agent.GAIAAgent(client=object(), environment={"AGENT_BACKEND": "hf"})
        with self.assertRaisesRegex(RuntimeError, "HF_LIVE_INFERENCE"):
            agent.GAIAAgent(client=object(), environment={
                "AGENT_BACKEND": "hf", "HF_TOKEN": "secret"})
        instance = agent.GAIAAgent(client=object(), environment={
            "AGENT_BACKEND": "hf", "HF_TOKEN": "secret", "HF_LIVE_INFERENCE": "1"})
        self.assertIn("Qwen", instance.model)

    def test_local_backend_no_token_or_provider_call(self):
        fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=
                SimpleNamespace(content="FINAL ANSWER: 42", tool_calls=[]))]))))
        bot = agent.GAIAAgent(client=fake, environment={})
        self.assertEqual(bot.answer("What is the answer?"), "42")

    def test_named_wikipedia_source_is_retrieved_before_reasoning(self):
        create = unittest.mock.Mock()
        bot = agent.GAIAAgent(client=SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create))), environment={})
        evidence = "MATCHING TABLE ROW COUNT FOR 2000-2009: 3"
        with patch.object(agent, "wikipedia", return_value=evidence) as wiki:
            self.assertEqual(bot.answer("How many? Use English Wikipedia."), "3")
        wiki.assert_called_once()
        create.assert_not_called()

    def test_calculator_tool_call_then_answer(self):
        calls = []
        tool_call = SimpleNamespace(id="abc", function=SimpleNamespace(
            name="calculate", arguments='{"expression": "6 * 7"}'))

        def respond(**kwargs):
            calls.append(kwargs)
            message = (SimpleNamespace(content=None, tool_calls=[tool_call])
                       if len(calls) == 1 else SimpleNamespace(content="42", tool_calls=[]))
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

        bot = agent.GAIAAgent(client=SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=respond))), environment={})
        self.assertEqual(bot.answer("Multiply 6 by 7"), "42")
        self.assertEqual(calls[1]["messages"][-1]["content"], "42")

    def test_missing_tool_dependency_stops_instead_of_fabricating(self):
        tool_call = SimpleNamespace(id="abc", function=SimpleNamespace(
            name="search_web", arguments='{"query": "evidence"}'))
        fake = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(
            create=lambda **kwargs: SimpleNamespace(choices=[SimpleNamespace(message=
                SimpleNamespace(content=None, tool_calls=[tool_call]))]))))
        bot = agent.GAIAAgent(client=fake, environment={})
        missing = ModuleNotFoundError("No module named 'ddgs'", name="ddgs")
        with patch.object(agent, "search_web", side_effect=missing), self.assertRaisesRegex(
                RuntimeError, "ddgs"):
            bot.answer("Find evidence")

    def test_search_snippet_cannot_be_used_without_source_verification(self):
        tool_call = SimpleNamespace(id="search", function=SimpleNamespace(
            name="search_web", arguments='{"query": "fact"}'))
        messages = [
            SimpleNamespace(content=None, tool_calls=[tool_call]),
            SimpleNamespace(content="42", tool_calls=[]),
            SimpleNamespace(content="42", tool_calls=[]),
        ]
        create = Mock(side_effect=[SimpleNamespace(choices=[SimpleNamespace(message=item)])
                                   for item in messages])
        bot = agent.GAIAAgent(client=SimpleNamespace(chat=SimpleNamespace(
            completions=SimpleNamespace(create=create))), environment={})
        with patch.object(agent, "search_web", return_value="snippet"), self.assertRaisesRegex(
                agent.ModelOutputError, "not verified"):
            bot.answer("Find the fact")
        self.assertIn("Call read_web_page", create.call_args_list[2].kwargs["messages"][-1]["content"])


class GaiaBenchmarkTests(unittest.TestCase):
    def test_answer_validation_flags_only_clear_format_failures(self):
        self.assertIn("repetition", benchmark.answer_issue("List vegetables", "milk " * 25))
        self.assertIn("three-letter", benchmark.answer_issue(
            "Give the three-letter IOC country code", "NL"))
        self.assertIn("three-letter", benchmark.answer_issue(
            "Give the IOC country code as your answer", "NL"))
        self.assertIsNone(benchmark.answer_issue("Give only the first name", "Bartłomiej"))
        self.assertIn("prose", benchmark.answer_issue(
            "Alphabetize the vegetables as a comma separated list",
            "Here are the vegetables:\nbroccoli, celery"))
        self.assertIsNone(benchmark.answer_issue("Who?", "Ralf"))

    def test_answer_constraints_and_deterministic_formatting(self):
        question = "Please alphabetize the ingredients in a comma separated list."
        self.assertEqual(benchmark.normalize_answer(question, "salt, apples"), "apples, salt")
        self.assertIsNone(benchmark.answer_issue(question, "apples, salt"))
        alphabetical = "Provide a comma separated list in alphabetical order."
        self.assertEqual(benchmark.normalize_answer(alphabetical, "b,c"), "b, c")
        self.assertIn("numeric", benchmark.answer_issue("What is the final numeric output?", "forty"))
        self.assertIn("positive", benchmark.answer_issue("How many at bats did he have?", "0"))
        self.assertIn("last names", benchmark.answer_issue(
            "Give Pitcher Before, Pitcher After, last names only", "Smith"))
        self.assertIn("person name", benchmark.answer_issue("Who nominated the article?", "47"))
        self.assertIn("could not determine", benchmark.answer_issue(
            "Who nominated it?", "The provided evidence does not contain the specific information."))
        self.assertEqual(
            benchmark.normalize_answer("What is the first name?", "Claus Peter Flor"), "Claus"
        )

    def test_trailing_final_numeric_answer_is_normalized(self):
        question = "What is the final numeric output from the attached Python code?"
        self.assertEqual(benchmark.normalize_answer(
            question, "The successful branch returns zero.\n\n**Final answer: 0**"), "0")
        self.assertEqual(benchmark.normalize_answer(question, "The output is 0"), "The output is 0")

    def test_quoted_question_echo_is_removed_from_response(self):
        question = 'What does he say in response to the question "Isn\'t that hot?"'
        self.assertEqual(
            benchmark.normalize_answer(question, "Isn't that hot? Extremely."), "Extremely."
        )

    def test_attachment_uses_official_endpoint_and_preserves_filename(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.raise_for_status.return_value = None
        response.iter_content.return_value = [b"print(42)"]
        with tempfile.TemporaryDirectory() as temporary, patch(
                "requests.get", return_value=response) as get:
            path = benchmark.attachment_for("abc-123", "Original code.py", temporary)
            self.assertEqual(Path(path).read_bytes(), b"print(42)")
            self.assertEqual(Path(path).name, "Original code.py")
        self.assertEqual(get.call_args.args[0], benchmark.BASE + "/files/abc-123")
        self.assertNotIn("headers", get.call_args.kwargs)

    def test_attachment_uses_private_local_file_without_network(self):
        with tempfile.TemporaryDirectory() as temporary:
            local = Path(temporary) / "private"
            local.mkdir()
            expected = local / "evidence.xlsx"
            expected.write_bytes(b"spreadsheet")
            with patch("requests.get") as get:
                path = benchmark.attachment_for(
                    "abc-123", "evidence.xlsx", temporary, local
                )
            self.assertEqual(Path(path), expected.resolve())
            get.assert_not_called()

    def test_missing_private_file_falls_back_to_official_endpoint(self):
        response = Mock()
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        response.raise_for_status.return_value = None
        response.iter_content.return_value = [b"audio"]
        with tempfile.TemporaryDirectory() as temporary, patch(
                "requests.get", return_value=response) as get:
            local = Path(temporary) / "private"
            local.mkdir()
            path = benchmark.attachment_for(
                "abc-123", "missing.mp3", temporary, local
            )
            self.assertEqual(Path(path).read_bytes(), b"audio")
        self.assertEqual(get.call_args.args[0], benchmark.BASE + "/files/abc-123")

    def test_attachment_403_is_reported_without_restricted_fallback(self):
        denied = Mock()
        denied.__enter__ = Mock(return_value=denied)
        denied.__exit__ = Mock(return_value=False)
        denied.raise_for_status.side_effect = __import__("requests").HTTPError(
            response=SimpleNamespace(status_code=403))
        with tempfile.TemporaryDirectory() as temporary, patch(
                "requests.get", return_value=denied) as get, self.assertRaisesRegex(
                benchmark.AttachmentDownloadError, "HTTP 403"):
            benchmark.attachment_for("abc-123", "data.xlsx", temporary)
        self.assertEqual(get.call_count, 1)

    def test_attachment_connection_failure_is_reported_accurately(self):
        with tempfile.TemporaryDirectory() as temporary, patch(
                "requests.get", side_effect=__import__("requests").ConnectionError()) as get:
            with self.assertRaisesRegex(benchmark.AttachmentDownloadError, "unavailable"):
                benchmark.attachment_for("abc-123", "data.xlsx", temporary)
        self.assertEqual(get.call_count, 1)

    def test_question_format_checked(self):
        fake = SimpleNamespace(raise_for_status=lambda: None, json=lambda: ["bad"])
        with patch.dict(sys.modules, {"requests": SimpleNamespace(get=lambda *a, **k: fake)}):
            with self.assertRaises(ValueError):
                benchmark.questions()

    def test_evaluation_keeps_failure_explicit(self):
        class FakeAgent:
            def answer(self, question, attachment=None):
                if question == "bad":
                    raise RuntimeError("Do not hallucinate")
                return "good answer"
        with patch.object(benchmark, "questions", return_value=[
            {"task_id": "one", "question": "ok"},
            {"task_id": "two", "question": "bad"}]):
            results = benchmark.evaluate(FakeAgent())
        self.assertEqual(results[0]["submitted_answer"], "good answer")
        self.assertEqual(results[1]["submitted_answer"], "")
        self.assertEqual(results[1]["error"], "RuntimeError")
        self.assertEqual(results[1]["error_message"], "Do not hallucinate")
        self.assertEqual(results[1]["question"], "bad")

    def test_invalid_model_answer_is_failed_and_retained_for_review(self):
        fake = SimpleNamespace(answer=lambda question, attachment=None: "milk " * 30)
        results = benchmark.evaluate_items(fake, [{"task_id": "one", "question": "Q"}])
        self.assertEqual(results[0]["error"], "AnswerValidationError")
        self.assertIn("repetition", results[0]["error_message"])
        self.assertTrue(results[0]["candidate_answer"].startswith("milk"))
        self.assertEqual(results[0]["submitted_answer"], "")

    def test_invalid_attachment_path_rejected_before_network(self):
        with self.assertRaisesRegex(ValueError, "task ID"):
            benchmark.attachment_for("../../etc", "a.txt", "/tmp")
        with patch("requests.get") as get, self.assertRaisesRegex(
                ValueError, "filename"):
            benchmark.attachment_for("abc-123", "../secret.txt", "/tmp")
        get.assert_not_called()

    def test_submissions_allow_partial_and_skip_failed_answers(self):
        valid = [{"task_id": str(i), "submitted_answer": "answer"} for i in range(20)]
        url = "https://huggingface.co/spaces/test/agent/tree/main"
        recorded = {}

        def fake_post(url, json, timeout):
            recorded.update(data=json)
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"score": 0})

        partial = valid[:1] + [
            {"task_id": "failed", "submitted_answer": "", "error": "RuntimeError"},
            {"task_id": "warning", "question": "Q", "submitted_answer": "maybe",
             "review_warning": "review"},
        ]
        with patch.dict(sys.modules, {"requests": SimpleNamespace(post=fake_post)}):
            benchmark.submit("test", url, partial)
        self.assertEqual(recorded["data"]["answers"], [valid[0]])

        with self.assertRaisesRegex(ValueError, "No valid answers"):
            benchmark.submit("test", url, [{"task_id": "19", "submitted_answer": ""}])
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            benchmark.submit("test", url, [valid[0], valid[0]])
        with self.assertRaisesRegex(ValueError, "public Hugging Face"):
            benchmark.submit("test", url.replace("huggingface.co", "huggingface.co.evil"), valid)

    def test_valid_submission_posts_expected_payload(self):
        valid = [{"task_id": str(i), "submitted_answer": "yes"} for i in range(20)]
        recorded = {}

        def fake_post(url, json, timeout):
            recorded.update(url=url, data=json, timeout=timeout)
            return SimpleNamespace(raise_for_status=lambda: None, json=lambda: {"score": 0.3})

        with patch.dict(sys.modules, {"requests": SimpleNamespace(post=fake_post)}):
            response = benchmark.submit("test", "https://huggingface.co/spaces/test/agent/tree/main", valid)
        self.assertEqual(response["score"], 0.3)
        self.assertEqual(len(recorded["data"]["answers"]), 20)
        self.assertEqual(recorded["url"], benchmark.BASE + "/submit")


class GaiaCliTests(unittest.TestCase):
    def test_repository_dotenv_is_loaded_without_overriding_shell(self):
        with patch.object(cli, "load_dotenv") as load_dotenv:
            cli.load_environment()
        expected = Path(cli.__file__).resolve().parents[2] / ".env"
        load_dotenv.assert_called_once_with(dotenv_path=expected, override=False)

    def test_run_saves_results_without_submitting(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = str(Path(temporary) / "answers.json")
            args = SimpleNamespace(limit=1, output=output)
            item = {"task_id": "one", "question": "Q"}
            with patch.object(cli, "questions", return_value=[item]), patch.object(
                    cli, "GAIAAgent", return_value=object()), patch.object(
                    cli, "evaluate_items", return_value=[{
                        "task_id": "one", "question": "Q", "file_name": "",
                        "submitted_answer": "A"}]):
                self.assertEqual(cli.run_command(args), 0)
            saved = cli.load_run(output)
            self.assertEqual(saved["results"][0]["submitted_answer"], "A")
            self.assertEqual(saved["format_version"], 1)

    def test_run_can_skip_a_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = str(Path(temporary) / "answers.json")
            items = [
                {"task_id": "keep", "question": "Q1"},
                {"task_id": "skip", "question": "Q2"},
            ]
            args = SimpleNamespace(
                limit=20, output=output, questions_file=None,
                skip_task_id=["skip"], attachments_dir="attachments")
            replacement = [{"task_id": "keep", "question": "Q1",
                            "file_name": "", "submitted_answer": "A"}]
            with patch.object(cli, "questions", return_value=items), patch.object(
                    cli, "GAIAAgent", return_value=object()), patch.object(
                    cli, "evaluate_items", return_value=replacement) as evaluate_selected:
                self.assertEqual(cli.run_command(args), 0)
            self.assertEqual(evaluate_selected.call_args.args[1], [items[0]])
            self.assertEqual(cli.load_run(output)["results"], replacement)

    def test_retry_replaces_only_failed_records(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = str(Path(temporary) / "answers.json")
            cli.save_run(output, [
                {"task_id": "ok", "question": "Q1", "submitted_answer": "A"},
                {"task_id": "bad", "question": "Q2", "submitted_answer": "",
                 "error": "RuntimeError", "error_message": "failed"},
            ])
            args = SimpleNamespace(answers=output, output=None, task_id=None, suspicious=False)
            replacement = [{"task_id": "bad", "question": "Q2", "file_name": "",
                            "submitted_answer": "B"}]
            with patch.object(cli, "GAIAAgent", return_value=object()), patch.object(
                    cli, "evaluate_items", return_value=replacement):
                self.assertEqual(cli.retry_command(args), 0)
            results = cli.load_run(output)["results"]
            self.assertEqual([item["submitted_answer"] for item in results], ["A", "B"])
            self.assertEqual(results[1]["attempt_history"][0]["error_message"], "failed")

    def test_retry_can_select_answered_task(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = str(Path(temporary) / "answers.json")
            cli.save_run(output, [
                {"task_id": "one", "question": "Q1", "submitted_answer": "old"},
                {"task_id": "two", "question": "Q2", "submitted_answer": "keep"},
            ])
            args = SimpleNamespace(answers=output, output=None, task_id=["one"],
                                   suspicious=False)
            replacement = [{"task_id": "one", "question": "Q1", "file_name": "",
                            "submitted_answer": "new"}]
            with patch.object(cli, "GAIAAgent", return_value=object()), patch.object(
                    cli, "evaluate_items", return_value=replacement):
                self.assertEqual(cli.retry_command(args), 0)
            answers = [item["submitted_answer"] for item in cli.load_run(output)["results"]]
            self.assertEqual(answers, ["new", "keep"])
            history = cli.load_run(output)["results"][0]["attempt_history"]
            self.assertEqual(history[0]["submitted_answer"], "old")

    def test_submit_requires_explicit_confirmation_before_api_call(self):
        args = SimpleNamespace(confirm_submit=False, answers="missing.json",
                               username="test", code_url="https://example.com")
        with patch.object(cli, "submit") as send, self.assertRaisesRegex(
                ValueError, "confirm-submit"):
            cli.submit_command(args)
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
