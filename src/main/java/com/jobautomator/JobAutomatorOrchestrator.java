package com.jobautomator;

import io.agentscope.core.agent.Agent;
import io.agentscope.core.message.Msg;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.List;
import java.util.Map;
import java.util.HashMap;

import io.agentscope.extensions.model.openai.OpenAIChatModel;
import io.agentscope.core.message.MsgRole;
import io.agentscope.core.message.TextBlock;

/**
 * Reactive Multi-Agent Orchestrator for JobAutomator AI using AgentScope Java.
 * Built with Project Reactor (non-blocking Mono/Flux pipelines).
 */
public class JobAutomatorOrchestrator {
    private static final Logger log = LoggerFactory.getLogger(JobAutomatorOrchestrator.class);

    private final String openaiApiKey;
    private final String supabaseUrl;
    private final String supabaseKey;
    private final OpenAIChatModel chatModel;

    public JobAutomatorOrchestrator() {
        this.openaiApiKey = System.getenv().getOrDefault("OPENAI_API_KEY", "");
        this.supabaseUrl = System.getenv().getOrDefault("SUPABASE_URL", "");
        this.supabaseKey = System.getenv().getOrDefault("SUPABASE_KEY", "");
        
        this.chatModel = OpenAIChatModel.builder()
                .apiKey(this.openaiApiKey.isEmpty() ? "dummy-key" : this.openaiApiKey)
                .modelName("gpt-4o-mini")
                .build();
    }

    /**
     * Executes the reactive job search, tailoring, and application pipeline.
     *
     * @param targetKeywords List of search keywords (e.g., "Java Developer", "AI Engineer")
     * @param targetLocation Location criteria (e.g., "Remote", "Brasil")
     * @return Mono emission of completion status summary
     */
    public Mono<Map<String, Object>> processJobApplicationsPipeline(List<String> targetKeywords, String targetLocation) {
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
                .onErrorResume(e -> {
                    log.error("Failed to execute job application pipeline", e);
                    return Mono.just(Map.<String, Object>of(
                            "status", "FAILED",
                            "error", e.getMessage()
                    ));
                });
    }

    private Flux<Map<String, Object>> searchJobsForKeyword(String keyword, String location) {
        log.info("Scraping job listings for keyword: {}...", keyword);
        // Reactive mock emission representing scraped LinkedIn postings
        Map<String, Object> sampleJob = Map.of(
                "jobId", "linkedin-102938",
                "title", keyword + " Specialist",
                "company", "Tech Global",
                "applyUrl", "https://www.linkedin.com/jobs/search/?keywords=" + keyword,
                "isEasyApply", true
        );
        return Flux.just(sampleJob);
    }

    private Mono<Map<String, Object>> evaluateJobMatchScore(Map<String, Object> job) {
        log.info("Evaluating AI match score for job: {}", job.get("title"));
        
        String prompt = "Evaluate the match score (0 to 100) for a job posting. Return ONLY a number.\n" +
                "Job Title: " + job.get("title") + "\n" +
                "Company: " + job.get("company") + "\n" +
                "My profile: Java Developer with Reactive Programming experience.";
                
        Msg userMsg = Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder().text(prompt).build())
                .name("user")
                .build();

        return chatModel.generate(List.of(userMsg), null, null)
                .map(response -> {
                    Map<String, Object> updated = new HashMap<>(job);
                    try {
                        double score = Double.parseDouble(response.getText().replaceAll("[^0-9.]", "").trim());
                        updated.put("matchScore", score);
                        log.info("AI returned match score: {} for job: {}", score, job.get("title"));
                    } catch (Exception e) {
                        log.warn("Failed to parse score: {}", response.getText());
                        updated.put("matchScore", 50.0);
                    }
                    return updated;
                })
                .onErrorResume(e -> {
                    log.error("AI Evaluation failed", e);
                    Map<String, Object> updated = new HashMap<>(job);
                    updated.put("matchScore", 50.0);
                    return Mono.just(updated);
                });
    }

    private Mono<Map<String, Object>> tailorResumeAndCoverLetter(Map<String, Object> job) {
        log.info("Tailoring ATS resume and Cover Letter via AI for job: {}", job.get("title"));
        
        String prompt = "Generate a short, tailored cover letter (2 paragraphs) for the following job in Portuguese.\n" +
                "Job Title: " + job.get("title") + "\n" +
                "Company: " + job.get("company");
                
        Msg userMsg = Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder().text(prompt).build())
                .name("user")
                .build();

        return chatModel.generate(List.of(userMsg), null, null)
                .map(response -> {
                    Map<String, Object> updated = new HashMap<>(job);
                    updated.put("tailoredResumeId", "res-" + System.currentTimeMillis());
                    updated.put("coverLetterText", response.getText());
                    log.info("AI Cover Letter generated successfully.");
                    return updated;
                })
                .onErrorResume(e -> {
                    log.error("AI Cover Letter generation failed", e);
                    Map<String, Object> updated = new HashMap<>(job);
                    updated.put("tailoredResumeId", "res-" + System.currentTimeMillis());
                    updated.put("coverLetterText", "Prezados recrutadores, me candidato à vaga...");
                    return Mono.just(updated);
                });
    }

    private Mono<Map<String, Object>> triggerBrowserGymAutoApply(Map<String, Object> jobData) {
        log.info("Triggering BrowserGym auto-apply sub-agent for job: {}", jobData.get("title"));
        
        return Mono.fromCallable(() -> {
            // Invokes Python BrowserGym service via process execution or API
            ProcessBuilder pb = new ProcessBuilder(
                    ".venv/Scripts/python.exe", "src/browsergym_service.py"
            );
            Process process = pb.start();
            int exitCode = process.waitFor();
            
            Map<String, Object> updated = new HashMap<>(jobData);
            updated.put("applicationStatus", exitCode == 0 ? "SUBMITTED" : "REQUIRES_MANUAL");
            return updated;
        }).onErrorResume(e -> {
            log.error("BrowserGym execution encountered an error", e);
            Map<String, Object> updated = new HashMap<>(jobData);
            updated.put("applicationStatus", "FAILED");
            updated.put("error", e.getMessage());
            return Mono.<Map<String, Object>>just(updated);
        });
    }
}

