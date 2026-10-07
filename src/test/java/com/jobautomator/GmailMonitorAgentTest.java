package com.jobautomator;

import com.jobautomator.ratelimit.ReactiveRateLimiter;
import io.agentscope.core.message.TextBlock;
import io.agentscope.core.model.ChatResponse;
import io.agentscope.extensions.model.openai.OpenAIChatModel;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.DisplayName;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;
import reactor.core.publisher.Flux;
import reactor.test.StepVerifier;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.when;

@ExtendWith(MockitoExtension.class)
class GmailMonitorAgentTest {

    @Mock
    private OpenAIChatModel chatModel;

    private GmailMonitorAgent agent;

    @BeforeEach
    void setUp() {
        agent = new GmailMonitorAgent(chatModel, new ReactiveRateLimiter());
    }

    @Test
    @DisplayName("Should classify interview invitation email correctly")
    void shouldClassifyInterviewInvite() {
        ChatResponse mockResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("Classification: INTERVIEW_INVITE\nPlease choose a slot on Calendly.").build()))
                .build();

        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.just(mockResponse));

        StepVerifier.create(agent.classifyEmail("Interview Invitation - Senior Java Role", "We would love to invite you for an interview.", "recruiter@tech.com"))
                .assertNext(res -> {
                    assertThat(res).containsEntry("classification", "INTERVIEW_INVITE");
                    assertThat(res).containsEntry("sender", "recruiter@tech.com");
                    assertThat(res).containsEntry("status", "SUCCESS");
                    assertThat((String) res.get("summary")).contains("Calendly");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should classify rejection email correctly")
    void shouldClassifyRejection() {
        ChatResponse mockResponse = ChatResponse.builder()
                .content(List.of(TextBlock.builder().text("Classification: REJECTION\nWe decided to move forward with other candidates.").build()))
                .build();

        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.just(mockResponse));

        StepVerifier.create(agent.classifyEmail("Update regarding your application", "Thank you for applying, but we will not proceed.", "no-reply@company.com"))
                .assertNext(res -> {
                    assertThat(res).containsEntry("classification", "REJECTION");
                    assertThat(res).containsEntry("status", "SUCCESS");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should reject execution if both subject and body are null")
    void shouldRejectNullSubjectAndBody() {
        StepVerifier.create(agent.classifyEmail(null, null, "sender@test.com"))
                .assertNext(res -> {
                    assertThat(res).containsEntry("status", "FAILED");
                    assertThat(res).containsEntry("errorCategory", "INVALID_INPUT");
                    assertThat(res).containsEntry("classification", "UNKNOWN");
                })
                .verifyComplete();
    }

    @Test
    @DisplayName("Should handle LLM failure gracefully with UNKNOWN classification fallback")
    void shouldHandleLlmFailureGracefully() {
        when(chatModel.stream(any(), any(), any()))
                .thenReturn(Flux.error(new RuntimeException("OpenAI connection timeout")));

        StepVerifier.create(agent.classifyEmail("Subject", "Body", "hr@company.com"))
                .assertNext(res -> {
                    assertThat(res).containsEntry("status", "FAILED");
                    assertThat(res).containsEntry("classification", "UNKNOWN");
                    assertThat(res).containsEntry("sender", "hr@company.com");
                })
                .verifyComplete();
    }
}
