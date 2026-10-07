package com.jobautomator;

import com.jobautomator.exception.CentralizedErrorHandler;
import com.jobautomator.ratelimit.ReactiveRateLimiter;
import com.jobautomator.ratelimit.ServiceName;
import io.agentscope.core.message.ContentBlock;
import io.agentscope.core.message.Msg;
import io.agentscope.core.message.MsgRole;
import io.agentscope.core.message.TextBlock;
import io.agentscope.core.model.ChatResponse;
import io.agentscope.extensions.model.openai.OpenAIChatModel;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import reactor.core.publisher.Mono;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

/**
 * Reactive LinkedIn Profile Scanner Agent using AgentScope Java.
 * Scans, audits, and optimizes candidate LinkedIn profile data with AI reasoning,
 * rate limiting protection, and centralized exception handling.
 */
public class LinkedInProfileScannerAgent {
    private static final Logger log = LoggerFactory.getLogger(LinkedInProfileScannerAgent.class);

    private final OpenAIChatModel chatModel;
    private final ReactiveRateLimiter rateLimiter;

    public LinkedInProfileScannerAgent() {
        this(null, new ReactiveRateLimiter());
    }

    public LinkedInProfileScannerAgent(OpenAIChatModel chatModel, ReactiveRateLimiter rateLimiter) {
        String openaiApiKey = System.getenv().getOrDefault("OPENAI_API_KEY", "dummy-key");
        this.chatModel = (chatModel != null) ? chatModel : OpenAIChatModel.builder()
                .apiKey(openaiApiKey.isEmpty() ? "dummy-key" : openaiApiKey)
                .modelName("gpt-4o-mini")
                .build();
        this.rateLimiter = Objects.requireNonNullElseGet(rateLimiter, ReactiveRateLimiter::new);
    }

    public Mono<Map<String, Object>> scanProfile(Map<String, Object> profileData) {
        if (profileData == null || profileData.isEmpty()) {
            return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                    new IllegalArgumentException("Profile data cannot be null or empty"),
                    "scanProfile",
                    Map.of("scanStatus", "FAILED")
            ));
        }

        log.info("Starting LinkedIn profile scan...");

        String prompt = "Review the following LinkedIn profile data and point out any errors, " +
                "missing sections, or areas for improvement (e.g., missing summary, weak headline, lacking skills). " +
                "Also, address whether having an incomplete or bad profile influences the success when creating an account and starting to use LinkedIn.\n" +
                "Profile Data: " + profileData.toString() + "\n" +
                "Provide a detailed analysis, pinpointing specific errors and recommendations.";

        Msg userMsg = Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder().text(prompt).build())
                .name("user")
                .build();

        return rateLimiter.acquire(ServiceName.LINKEDIN_SCRAPING)
                .then(rateLimiter.acquire(ServiceName.OPENAI_API))
                .then(chatModel.stream(List.of(userMsg), null, null)
                        .reduce("", (acc, chunk) -> acc + extractText(chunk))
                        .map(text -> {
                            Map<String, Object> result = new HashMap<>(profileData);
                            result.put("profileAnalysis", text);
                            result.put("scanStatus", "COMPLETED");
                            result.put("status", "SUCCESS");
                            log.info("Profile scan completed successfully.");
                            return result;
                        })
                )
                .onErrorResume(e -> {
                    Map<String, Object> fallback = new HashMap<>(profileData);
                    fallback.put("scanStatus", "FAILED");
                    return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                            e, "scanProfile", fallback
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
