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
 * Reactive Gmail Monitor Agent using AgentScope Java.
 * Scans, processes, and classifies recruitment emails with AI reasoning,
 * rate limiting protection, and centralized exception handling.
 */
public class GmailMonitorAgent {
    private static final Logger log = LoggerFactory.getLogger(GmailMonitorAgent.class);

    private final OpenAIChatModel chatModel;
    private final ReactiveRateLimiter rateLimiter;

    public GmailMonitorAgent() {
        this(null, new ReactiveRateLimiter());
    }

    public GmailMonitorAgent(OpenAIChatModel chatModel, ReactiveRateLimiter rateLimiter) {
        String openaiApiKey = System.getenv().getOrDefault("OPENAI_API_KEY", "dummy-key");
        this.chatModel = (chatModel != null) ? chatModel : OpenAIChatModel.builder()
                .apiKey(openaiApiKey.isEmpty() ? "dummy-key" : openaiApiKey)
                .modelName("gpt-4o-mini")
                .build();
        this.rateLimiter = Objects.requireNonNullElseGet(rateLimiter, ReactiveRateLimiter::new);
    }

    public Mono<Map<String, Object>> classifyEmail(String emailSubject, String emailBody, String sender) {
        if (emailSubject == null && emailBody == null) {
            return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                    new IllegalArgumentException("Email subject and body cannot both be null"),
                    "classifyEmail",
                    Map.of("classification", "UNKNOWN")
            ));
        }

        String safeSubject = Objects.requireNonNullElse(emailSubject, "(No Subject)");
        String safeBody = Objects.requireNonNullElse(emailBody, "(No Content)");
        String safeSender = Objects.requireNonNullElse(sender, "unknown@sender.com");

        log.info("Classifying email from: {} with subject: {}", safeSender, safeSubject);

        String prompt = "Analyze the following email from a job application process.\n" +
                "Classify it strictly as one of: INTERVIEW_INVITE, STATUS_UPDATE, REJECTION.\n" +
                "Provide a brief summary of the next steps.\n" +
                "Email Subject: " + safeSubject + "\n" +
                "Email Body: " + safeBody;

        Msg userMsg = Msg.builder()
                .role(MsgRole.USER)
                .content(TextBlock.builder().text(prompt).build())
                .name("user")
                .build();

        return rateLimiter.acquire(ServiceName.GMAIL_MONITOR)
                .then(rateLimiter.acquire(ServiceName.OPENAI_API))
                .then(chatModel.stream(List.of(userMsg), null, null)
                        .reduce("", (acc, chunk) -> acc + extractText(chunk))
                        .map(text -> {
                            String classification = "STATUS_UPDATE";
                            if (text.contains("INTERVIEW_INVITE")) classification = "INTERVIEW_INVITE";
                            else if (text.contains("REJECTION")) classification = "REJECTION";

                            Map<String, Object> result = new HashMap<>();
                            result.put("classification", classification);
                            result.put("summary", text);
                            result.put("sender", safeSender);
                            result.put("subject", safeSubject);
                            result.put("status", "SUCCESS");
                            return result;
                        })
                )
                .onErrorResume(e -> {
                    Map<String, Object> fallback = new HashMap<>();
                    fallback.put("classification", "UNKNOWN");
                    fallback.put("sender", safeSender);
                    fallback.put("subject", safeSubject);
                    return Mono.just(CentralizedErrorHandler.formatErrorResponse(
                            e, "classifyEmail", fallback
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
