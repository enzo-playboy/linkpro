package com.jobautomator;

import com.jobautomator.exception.CentralizedErrorHandler;
import com.jobautomator.ratelimit.ReactiveRateLimiter;
import com.jobautomator.ratelimit.ServiceName;
import com.jobautomator.security.SecureProcessExecutor;
import io.agentscope.core.message.ContentBlock;
import io.agentscope.core.message.Msg;
import io.agentscope.core.message.MsgRole;
import io.agentscope.core.message.TextBlock;
import io.agentscope.core.model.ChatResponse;
import io.agentscope.extensions.model.openai.OpenAIChatModel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * Reactive Multi-Agent Orchestrator for JobAutomator AI using AgentScope Java.
 * Built with Project Reactor (strictly non-blocking Mono/Flux pipelines).
 * Features:
 *  - Centralized Exception Handling & secret masking
 *  - Token-bucket Reactive Rate Limiting across all external services
 *  - Sanitized & non-blocking sub-process execution for BrowserGym
 */
public class JobAutomatorOrchestrator {
    private static final Logger log = LoggerFactory.getLogger(JobAutomatorOrchestrator.class);

    private final String openaiApiKey;
    private final String supabaseUrl;
    private final String supabaseKey;
    private final OpenAIChatModel chatModel;
    private final SecureProcessExecutor processExecutor;
    private final ReactiveRateLimiter rateLimiter;

    public JobAutomatorOrchestrator() {
        this(
                null,
                new SecureProcessExecutor(),
                new ReactiveRateLimiter()
        );
    }

    public JobAutomatorOrchestrator(OpenAIChatModel chatModel,
                                     SecureProcessExecutor processExecutor,
                                     ReactiveRateLimiter rateLimiter) {
        this.openaiApiKey = System.getenv().getOrDefault("OPENAI_API_KEY", "");
        this.supabaseUrl = System.getenv().getOrDefault("SUPABASE_URL", "");
        this.supabaseKey = System.getenv().getOrDefault("SUPABASE_KEY", "");

        this.chatModel = (chatModel != null) ? chatModel : OpenAIChatModel.builder()
                .apiKey(this.openaiApiKey.isEmpty() ? "dummy-key" : this.openaiApiKey)
                .modelName("gpt-4o-mini")
                .build();
        this.processExecutor = Objects.requireNonNullElseGet(processExecutor, SecureProcessExecutor::new);
        this.rateLimiter = Objects.requireNonNullElseGet(rateLimiter, ReactiveRateLimiter::new);
    }

    /**
     * Executes the reactive job search, tailoring, and application pipeline.
     *
     * @param targetKeywords List of search keywords (e.g., "Java Developer", "AI Engineer")
     * @param targetLocation Location criteria (e.g., "Remote", "Brasil")
     * @return Mono emission of completion status summary
     */
    public Mono<Map<String, Object>> processJobApplicationsPipeline(List<String> targetKeywords, String targetLocation) {
        if (targetKeywords == null || targetKeywords.isEmpty()) {
            return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                    new IllegalArgumentException("targetKeywords must not be null or empty"),
                    "processJobApplicationsPipeline",
                    Map.of("totalProcessed", 0)
            ));
        }
        if (targetLocation == null || targetLocation.isBlank()) {
            return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                    new IllegalArgumentException("targetLocation must not be null or blank"),
                    "processJobApplicationsPipeline",
                    Map.of("totalProcessed", 0)
            ));
        }

        log.info("Starting reactive job application pipeline for keywords: {} in {}", targetKeywords, targetLocation);

        return Flux.fromIterable(targetKeywords)
                .flatMap(keyword -> searchJobsForKeyword(keyword, targetLocation))
                .flatMap(this::evaluateJobMatchScore)
                .filter(job -> (double) job.getOrDefault("matchScore", 0.0) >= 75.0)
                .flatMap(this::tailorResumeAndCoverLetter)
                .flatMap(this::triggerBrowserGymAutoApply)
                .collectList()
                .map(results -> Map.<String, Object>of(
                        "totalProcessed", results.size(),
                        "results", results,
                        "status", "SUCCESS"
                ))
                .onErrorResume(e -> Mono.just(CentralizedErrorHandler.formatErrorResponse(
                        e, "processJobApplicationsPipeline", Map.of("totalProcessed", 0)
                )));
    }

    protected Flux<Map<String, Object>> searchJobsForKeyword(String keyword, String location) {
        return rateLimiter.acquire(ServiceName.LINKEDIN_SCRAPING)
                .thenMany(Flux.defer(() -> {
                    log.info("Scraping job listings for keyword: {} in location: {}", keyword, location);
                    Map<String, Object> sampleJob = Map.of(
                            "jobId", "linkedin-" + Math.abs(keyword.hashCode() % 1000000),
                            "title", keyword + " Specialist",
                            "company", "Tech Global",
                            "applyUrl", "https://www.linkedin.com/jobs/search/?keywords=" + keyword,
                            "isEasyApply", true
                    );
                    return Flux.just(sampleJob);
                }));
    }

    protected Mono<Map<String, Object>> evaluateJobMatchScore(Map<String, Object> job) {
        String prompt = "Evaluate the match score (0 to 100) for a job posting. Return ONLY a number.\n" +
                "Job Title: " + job.get("title") + "\n" +
                "Company: " + job.get("company") + "\n" +
                "My profile: Java Developer with Reactive Programming experience.";

        Msg userMsg = Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder().text(prompt).build())
                .name("user")
                .build();

        return rateLimiter.acquire(ServiceName.OPENAI_API)
                .then(chatModel.stream(List.of(userMsg), null, null)
                        .reduce("", (acc, chunk) -> acc + extractText(chunk))
                        .map(text -> {
                            Map<String, Object> updated = new HashMap<>(job);
                            try {
                                double score = Double.parseDouble(text.replaceAll("[^0-9.]", "").trim());
                                updated.put("matchScore", score);
                                log.info("AI returned match score: {} for job: {}", score, job.get("title"));
                            } catch (Exception e) {
                                log.warn("Failed to parse score: {}", text);
                                updated.put("matchScore", 50.0);
                            }
                            return updated;
                        })
                )
                .onErrorResume(e -> {
                    Map<String, Object> updated = new HashMap<>(job);
                    updated.put("matchScore", 50.0);
                    return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                            e, "evaluateJobMatchScore", updated
                    ));
                });
    }

    protected Mono<Map<String, Object>> tailorResumeAndCoverLetter(Map<String, Object> job) {
        String prompt = "Generate a short, tailored cover letter (2 paragraphs) for the following job in Portuguese.\n" +
                "Job Title: " + job.get("title") + "\n" +
                "Company: " + job.get("company");

        Msg userMsg = Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder().text(prompt).build())
                .name("user")
                .build();

        return rateLimiter.acquire(ServiceName.OPENAI_API)
                .then(chatModel.stream(List.of(userMsg), null, null)
                        .reduce("", (acc, chunk) -> acc + extractText(chunk))
                        .map(text -> {
                            Map<String, Object> updated = new HashMap<>(job);
                            updated.put("tailoredResumeId", "res-" + System.currentTimeMillis());
                            updated.put("coverLetterText", text);
                            log.info("AI Cover Letter generated successfully for: {}", job.get("title"));
                            return updated;
                        })
                )
                .onErrorResume(e -> {
                    Map<String, Object> updated = new HashMap<>(job);
                    updated.put("tailoredResumeId", "res-" + System.currentTimeMillis());
                    updated.put("coverLetterText", "Prezados recrutadores, me candidato à vaga...");
                    return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                            e, "tailorResumeAndCoverLetter", updated
                    ));
                });
    }

    protected Mono<Map<String, Object>> triggerBrowserGymAutoApply(Map<String, Object> jobData) {
        log.info("Triggering BrowserGym auto-apply sub-agent safely for job: {}", jobData.get("title"));

        String applyUrl = (String) jobData.getOrDefault("applyUrl", "https://www.linkedin.com/jobs");
        List<String> scriptArgs = List.of(
                "--apply",
                "--job-url=" + applyUrl
        );

        return rateLimiter.acquire(ServiceName.BROWSERGYM_APPLY)
                .then(processExecutor.executePythonScript("src/browsergym_service.py", scriptArgs))
                .map(result -> {
                    Map<String, Object> updated = new HashMap<>(jobData);
                    updated.put("applicationStatus", result.isSuccess() ? "SUBMITTED" : "REQUIRES_MANUAL");
                    updated.put("exitCode", result.exitCode());
                    return updated;
                })
                .onErrorResume(e -> {
                    Map<String, Object> updated = new HashMap<>(jobData);
                    updated.put("applicationStatus", "FAILED");
                    return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                            e, "triggerBrowserGymAutoApply", updated
                    ));
                });
    }

    private String extractText(ChatResponse response) {
        if (response.getContent() == null) return "";
        return response.getContent().stream()
                .filter(block -> block instanceof TextBlock)
                .map(block -> ((TextBlock) block).getText())
                .collect(Collectors.joining());
    }
}
