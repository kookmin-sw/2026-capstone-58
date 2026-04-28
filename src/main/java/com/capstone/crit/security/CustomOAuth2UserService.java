package com.capstone.crit.security;

import com.capstone.crit.entity.User;
import com.capstone.crit.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.oauth2.client.userinfo.DefaultOAuth2UserService;
import org.springframework.security.oauth2.client.userinfo.OAuth2UserRequest;
import org.springframework.security.oauth2.core.OAuth2AuthenticationException;
import org.springframework.security.oauth2.core.user.OAuth2User;
import org.springframework.stereotype.Service;

import java.util.Map;

@Service
@RequiredArgsConstructor
public class CustomOAuth2UserService extends DefaultOAuth2UserService {

    private final UserRepository userRepository;

    @Override
    public OAuth2User loadUser(OAuth2UserRequest userRequest) throws OAuth2AuthenticationException {
        OAuth2User oAuth2User = super.loadUser(userRequest);
        Map<String, Object> attributes = oAuth2User.getAttributes();

        String googleId = (String) attributes.get("sub");
        String email    = (String) attributes.get("email");
        String name     = (String) attributes.get("name");
        String picture  = (String) attributes.get("picture");

        // 신규 유저면 저장, 기존 유저면 그대로 (YouTube 정보는 SuccessHandler에서 갱신)
        userRepository.findByGoogleId(googleId).orElseGet(() ->
                userRepository.save(User.builder()
                        .googleId(googleId)
                        .email(email)
                        .name(name)
                        .profileImage(picture)
                        .build())
        );

        return oAuth2User;
    }
}
