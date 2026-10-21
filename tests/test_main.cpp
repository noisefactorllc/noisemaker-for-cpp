#include "test_harness.hpp"

#include <filesystem>
#include <fstream>
#include <map>
#include <set>
#include <string_view>

int main(int argc, char** argv) {
  std::vector<const test::Case*> selected;
  if (argc == 1) {
    for (const auto& item : test::cases()) selected.push_back(&item);
  } else {
    try {
      std::map<std::string, const test::Case*> indexed;
      for (const auto& item : test::cases()) {
        if (!indexed.emplace(item.name, &item).second) throw std::runtime_error("duplicate test ID");
      }
      if (argc == 2 && std::string_view(argv[1]) == "--list-tests") {
        for (const auto& entry : indexed) std::cout << entry.first << '\n';
        return 0;
      }
      if (argc != 3 || std::string_view(argv[1]) != "--test-ids-file") {
        throw std::runtime_error("expected --list-tests or --test-ids-file PATH");
      }
      if (!std::filesystem::is_regular_file(std::filesystem::symlink_status(argv[2]))) {
        throw std::runtime_error("test ID file must be a regular file");
      }
      std::ifstream input(argv[2]);
      if (!input) throw std::runtime_error("cannot read test ID file");
      std::set<std::string> seen;
      std::string name;
      while (std::getline(input, name)) {
        const auto found = indexed.find(name);
        if (found == indexed.end()) throw std::runtime_error("unknown test ID: " + name);
        if (!seen.insert(name).second) throw std::runtime_error("duplicate selected test ID: " + name);
        selected.push_back(found->second);
      }
      if (!input.eof() || selected.empty()) throw std::runtime_error("empty or unreadable test ID file");
    } catch (const std::exception& error) {
      std::cerr << "Test selection error: " << error.what() << '\n';
      return 2;
    }
  }
  int failures = 0;
  for (const auto* selected_case : selected) {
    const auto& test_case = *selected_case;
    try {
      test_case.function();
      std::cout << "PASS " << test_case.name << '\n';
    } catch (const std::exception& error) {
      ++failures;
      std::cerr << "FAIL " << test_case.name << ": " << error.what() << '\n';
    }
  }
  return failures == 0 ? 0 : 1;
}
