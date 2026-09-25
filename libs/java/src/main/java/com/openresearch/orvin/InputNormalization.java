package com.openresearch.orvin;

final class InputNormalization {
    private InputNormalization() { }

    static String normalize(String value) {
        int start = 0;
        int end = value.length();
        while (start < end && value.charAt(start) == ' ') start++;
        while (end > start && value.charAt(end - 1) == ' ') end--;
        StringBuilder result = new StringBuilder(end - start);
        for (int i = start; i < end; i++) {
            char c = value.charAt(i);
            result.append(c >= 'a' && c <= 'z' ? (char) (c - 'a' + 'A') : c);
        }
        return result.toString();
    }
}
