#ifndef SHIN_BOOK_H_
#define SHIN_BOOK_H_

#include <string>
#include <vector>
#include "move.h"
#include "position.h"

// A small, position-based book for reviewed Shin-Yonenaga-Gyoku moves.
class ShinBook {
 public:
  void ReadFromFile(const std::string& file_name);
  Move Probe(const Position& position) const;

 private:
  struct Entry {
    Position position;
    Move move;
  };
  std::vector<Entry> entries_;
};

#endif  // SHIN_BOOK_H_
