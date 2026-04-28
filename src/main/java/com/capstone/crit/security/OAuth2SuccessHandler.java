package com.capstone.crit.security;

import com.capstone.crit.entity.User;
import com.capstone.crit.repository.UserRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.core.Authentication;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClient;
import org.springframework.security.oauth2.client.OAuth2AuthorizedClientService;
import org.springframework.security.oauth2.client.authentication.OAuth2AuthenticationToken;
import org.springframework.security.web.authentication.SimpleUrlAuthenticationSuccessHandler;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;

@Slf4j
@Component
@RequiredArgsConstructor
public class OAuth2SuccessHandler extends SimpleUrlAuthenticationSuccessHandler {

    private final JwtTokenProvider jwtTokenProvider;
    private final UserRepository userRepository;
    private final OAuth2AuthorizedClientService authorizedClientService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${app.oauth2.redirect-url}")
    private String redirectUrl;

    @Override
    public void onAuthenticationSuccess(HttpServletRequest request,
                                        HttpServletResponse response,
                                        Authentication authentication) throws IOException {
        try {
            OAuth2AuthenticationToken oauthToken = (OAuth2AuthenticationToken) authentication;
            log.info("OAuth2 로그인 성공 - principalName: {}", oauthToken.getName());

            OAuth2AuthorizedClient client = authorizedClientService.loadAuthorizedClient(
                    oauthToken.getAuthorizedClientRegistrationId(),
                    oauthToken.getName()
            );

            if (client == null) {
                log.error("OAuth2AuthorizedClient가 null - 세션 문제 가능성");
                response.sendRedirect(redirectUrl + "?error=client_not_found");
                return;
            }

            String accessToken  = client.getAccessToken().getTokenValue();
            String refreshToken = client.getRefreshToken() != null
                    ? client.getRefreshToken().getTokenValue() : null;
            log.info("accessToken 획득 완료, refreshToken: {}", refreshToken != null ? "있음" : "없음");

            String googleId = oauthToken.getName();
            User user = userRepository.findByGoogleId(googleId).orElseThrow(
                    () -> new IllegalStateException("DB에 유저 없음: " + googleId)
            );
            log.info("유저 조회 완료 - userId: {}", user.getId());

            fetchAndSaveYoutubeInfo(user, accessToken);

            if (refreshToken != null) {
                user.updateRefreshToken(refreshToken);
                userRepository.save(user);
            }

            String jwt = jwtTokenProvider.generateToken(user.getId());
            log.info("JWT 발급 완료, 리다이렉트: {}", redirectUrl);
            getRedirectStrategy().sendRedirect(request, response, redirectUrl + "?token=" + jwt);

        } catch (Exception e) {
            log.error("OAuth2 성공 핸들러 처리 중 오류", e);
            response.sendRedirect(redirectUrl + "?error=server_error");
        }
    }

    private void fetchAndSaveYoutubeInfo(User user, String accessToken) {
        try {
            RestTemplate restTemplate = new RestTemplate();
            HttpHeaders headers = new HttpHeaders();
            headers.setBearerAuth(accessToken);

            ResponseEntity<String> response = restTemplate.exchange(
                    "https://www.googleapis.com/youtube/v3/channels?part=snippet,statistics&mine=true",
                    HttpMethod.GET,
                    new HttpEntity<>(headers),
                    String.class
            );

            JsonNode root  = objectMapper.readTree(response.getBody());
            JsonNode items = root.path("items");

            if (items.isEmpty()) {
                log.info("유저 {}는 YouTube 채널 없음", user.getEmail());
                return;
            }

            JsonNode item = items.get(0);
            user.updateYoutubeInfo(
                    item.path("id").asText(),
                    item.path("snippet").path("title").asText(),
                    item.path("snippet").path("description").asText(),
                    item.path("statistics").path("subscriberCount").asLong(),
                    item.path("statistics").path("videoCount").asLong(),
                    item.path("snippet").path("thumbnails").path("default").path("url").asText()
            );
            userRepository.save(user);

        } catch (Exception e) {
            log.warn("YouTube 채널 정보 조회 실패: {}", e.getMessage());
        }
    }
}
